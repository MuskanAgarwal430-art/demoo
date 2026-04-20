import cv2
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from core.dynamic_models import get_employee_model
from core.permissions import IsCompanyManager, BelongsToCompany
from .dataset_service import get_image_paths
from services.vector_db import ChromaDBService


class TrainEmployeeView(APIView):
    """
    Extract ArcFace embeddings for one employee and store in ChromaDB.
    Requires image_status = "approved".
    """
    permission_classes = [IsCompanyManager, BelongsToCompany]

    def post(self, request, company_code):
        employee_code = request.data.get("employee_code")
        if not employee_code:
            return Response({"detail": "employee_code is required."}, status=status.HTTP_400_BAD_REQUEST)

        Employee = get_employee_model(company_code.upper())
        try:
            emp = Employee.objects.get(employee_code=employee_code)
        except Employee.DoesNotExist:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

        if emp.image_status != "approved":
            return Response(
                {"detail": f"Images must be approved before training. Current status: {emp.image_status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_paths = get_image_paths(company_code, employee_code)
        if not image_paths:
            return Response({"detail": "No images found."}, status=status.HTTP_400_BAD_REQUEST)

        return _train_employee(emp, image_paths, company_code, employee_code)


class TrainAllView(APIView):
    """Train all approved employees for a company (runs via Celery)."""
    permission_classes = [IsCompanyManager, BelongsToCompany]

    def post(self, request, company_code):
        from apps.faces.tasks import train_all_employees_task
        task = train_all_employees_task.delay(company_code)
        return Response({"detail": "Training started.", "task_id": task.id})


class TrainingStatusView(APIView):
    permission_classes = [IsCompanyManager, BelongsToCompany]

    def get(self, request, company_code):
        from celery.result import AsyncResult
        task_id = request.query_params.get("task_id")
        if not task_id:
            return Response({"detail": "task_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = AsyncResult(task_id)
        return Response({"task_id": task_id, "status": result.status, "result": result.result})


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _train_employee(emp, image_paths: list, company_code: str, employee_code: str) -> Response:
    from ml.insightface_onnx import extract_embedding

    full_name = f"{emp.first_name} {emp.last_name}"
    stored = 0
    errors = []

    # Clear old embeddings first
    ChromaDBService.delete_employee_embeddings(company_code, employee_code)

    for idx, path in enumerate(image_paths):
        try:
            image = cv2.imread(path)
            if image is None:
                errors.append(f"Could not read image: {path}")
                continue

            embedding = extract_embedding(image)
            ChromaDBService.add_embedding(company_code, employee_code, embedding, idx, full_name)
            stored += 1
        except Exception as e:
            errors.append(f"Image {idx}: {str(e)}")

    if stored == 0:
        return Response(
            {"detail": "Training failed. No valid face detected in any image.", "errors": errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    emp.face_enrolled = True
    emp.chromadb_id = employee_code
    emp.image_status = "trained"
    emp.enrolled_at = timezone.now()
    emp.save()

    return Response({
        "detail": "Training complete.",
        "employee_code": employee_code,
        "embeddings_stored": stored,
        "errors": errors,
    })
