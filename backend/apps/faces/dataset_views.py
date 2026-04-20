from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from core.dynamic_models import get_employee_model
from core.permissions import IsCompanyManager, BelongsToCompany
from .dataset_service import (
    save_face_image, list_employee_images,
    delete_employee_image, delete_all_employee_images,
)


def _get_employee_or_404(company_code, employee_code):
    Employee = get_employee_model(company_code.upper())
    try:
        return Employee.objects.get(employee_code=employee_code)
    except Employee.DoesNotExist:
        return None


class CaptureImagesView(APIView):
    """Upload one or more face images for an employee."""
    permission_classes = [IsCompanyManager, BelongsToCompany]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, company_code):
        employee_code = request.data.get("employee_code")
        if not employee_code:
            return Response({"detail": "employee_code is required."}, status=status.HTTP_400_BAD_REQUEST)

        emp = _get_employee_or_404(company_code, employee_code)
        if not emp:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

        images = request.FILES.getlist("images")
        if not images:
            return Response({"detail": "No images uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        saved = []
        for img_file in images:
            result = save_face_image(company_code, employee_code, img_file)
            saved.append(result)

        # Update employee record
        emp.image_count = len(list_employee_images(company_code, employee_code))
        emp.image_status = "captured"
        emp.face_enrolled = False
        emp.save()

        return Response({"uploaded": len(saved), "images": saved}, status=status.HTTP_201_CREATED)


class ListImagesView(APIView):
    """List all face images for an employee."""
    permission_classes = [IsCompanyManager, BelongsToCompany]

    def get(self, request, company_code):
        employee_code = request.query_params.get("employee_code")
        if not employee_code:
            return Response({"detail": "employee_code is required."}, status=status.HTTP_400_BAD_REQUEST)

        emp = _get_employee_or_404(company_code, employee_code)
        if not emp:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

        images = list_employee_images(company_code, employee_code)
        return Response({"employee_code": employee_code, "count": len(images), "images": images})


class DeleteImageView(APIView):
    """Delete a single face image."""
    permission_classes = [IsCompanyManager, BelongsToCompany]

    def post(self, request, company_code):
        employee_code = request.data.get("employee_code")
        image_id = request.data.get("image_id")
        if not employee_code or not image_id:
            return Response({"detail": "employee_code and image_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        emp = _get_employee_or_404(company_code, employee_code)
        if not emp:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

        deleted = delete_employee_image(company_code, employee_code, image_id)
        if not deleted:
            return Response({"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND)

        emp.image_count = len(list_employee_images(company_code, employee_code))
        emp.save()
        return Response({"detail": "Image deleted."})


class DeleteAllImagesView(APIView):
    """Delete all face images for an employee."""
    permission_classes = [IsCompanyManager, BelongsToCompany]

    def post(self, request, company_code):
        employee_code = request.data.get("employee_code")
        if not employee_code:
            return Response({"detail": "employee_code is required."}, status=status.HTTP_400_BAD_REQUEST)

        emp = _get_employee_or_404(company_code, employee_code)
        if not emp:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

        delete_all_employee_images(company_code, employee_code)
        emp.image_count = 0
        emp.image_status = "pending"
        emp.face_enrolled = False
        emp.chromadb_id = ""
        emp.save()

        # Remove from ChromaDB
        from services.vector_db import ChromaDBService
        ChromaDBService.delete_employee_embeddings(company_code, employee_code)

        return Response({"detail": "All images deleted."})


class ApproveImagesView(APIView):
    """Admin approves face images so they can be trained."""
    permission_classes = [IsCompanyManager, BelongsToCompany]

    def post(self, request, company_code):
        employee_code = request.data.get("employee_code")
        if not employee_code:
            return Response({"detail": "employee_code is required."}, status=status.HTTP_400_BAD_REQUEST)

        emp = _get_employee_or_404(company_code, employee_code)
        if not emp:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

        if emp.image_count == 0:
            return Response({"detail": "No images to approve."}, status=status.HTTP_400_BAD_REQUEST)

        emp.image_status = "approved"
        emp.save()
        return Response({"detail": "Images approved.", "employee_code": employee_code})
