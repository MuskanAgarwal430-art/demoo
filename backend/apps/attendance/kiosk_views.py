import uuid
import base64
import logging
from datetime import date, datetime

from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from core.models import Company
from core.dynamic_models import get_employee_model, get_attendance_model, get_face_scan_model
from ml.face_recognizer import recognize_face

logger = logging.getLogger(__name__)


def _get_company(company_code: str):
    try:
        return Company.objects.get(company_code=company_code.upper(), is_active=True)
    except Company.DoesNotExist:
        return None


def _save_frame_image(company_code: str, b64_image: str) -> str:
    """Save the scan frame image to disk and return the relative path."""
    try:
        if b64_image.startswith("data:image"):
            b64_image = b64_image.split(",", 1)[1]
        import cv2
        import numpy as np
        from pathlib import Path

        img_bytes = base64.b64decode(b64_image)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        save_dir = Path(settings.MEDIA_ROOT) / "detections" / company_code.upper()
        save_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{timezone.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
        cv2.imwrite(str(save_dir / filename), image)
        return f"detections/{company_code.upper()}/{filename}"
    except Exception as e:
        logger.warning("Could not save frame image: %s", e)
        return ""


class KioskRecognizeView(APIView):
    """
    Public endpoint — no auth required.
    Accepts a base64 face image, identifies the employee, marks attendance.
    """
    permission_classes = [AllowAny]

    def post(self, request, company_code):
        company = _get_company(company_code)
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

        b64_image = request.data.get("face_image")
        if not b64_image:
            return Response({"detail": "face_image is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Run full recognition pipeline
        result = recognize_face(b64_image, company_code)

        frame_path = _save_frame_image(company_code, b64_image)
        FaceScan = get_face_scan_model(company_code.upper())

        if not result["success"]:
            # Log the failed scan
            FaceScan.objects.create(
                id=uuid.uuid4(),
                employee_code="",
                action="unrecognized",
                face_confidence=0.0,
                frame_image=frame_path,
                is_live=result.get("error") != "spoof_detected",
            )
            error_map = {
                "invalid_image": status.HTTP_400_BAD_REQUEST,
                "poor_quality": status.HTTP_400_BAD_REQUEST,
                "spoof_detected": status.HTTP_400_BAD_REQUEST,
                "no_face_detected": status.HTTP_400_BAD_REQUEST,
            }
            return Response(
                {"status": result["error"], "detail": result["detail"]},
                status=error_map.get(result["error"], status.HTTP_400_BAD_REQUEST),
            )

        if not result["matched"]:
            FaceScan.objects.create(
                id=uuid.uuid4(),
                employee_code="",
                action="unrecognized",
                face_confidence=result["confidence"],
                frame_image=frame_path,
                is_live=True,
            )
            return Response({
                "status": "not_recognized",
                "detail": "Face not recognized.",
                "confidence": result["confidence"],
            }, status=status.HTTP_200_OK)

        # Employee identified — mark attendance
        employee_code = result["employee_code"]
        Employee = get_employee_model(company_code.upper())
        Attendance = get_attendance_model(company_code.upper())

        try:
            emp = Employee.objects.get(employee_code=employee_code)
        except Employee.DoesNotExist:
            return Response({"detail": "Employee record not found."}, status=status.HTTP_404_NOT_FOUND)

        today = date.today()
        now = timezone.now()

        attendance, created = Attendance.objects.get_or_create(
            employee_code=employee_code,
            date=today,
            defaults={
                "id": uuid.uuid4(),
                "check_in": now,
                "check_in_confidence": result["confidence"],
                "status": _compute_status(company, now),
            },
        )

        if created:
            action = "check_in"
            FaceScan.objects.create(
                id=uuid.uuid4(),
                employee_code=employee_code,
                action="check_in",
                face_confidence=result["confidence"],
                frame_image=frame_path,
                is_live=True,
            )
        elif attendance.check_out is None:
            # Mark check-out
            attendance.check_out = now
            attendance.check_out_confidence = result["confidence"]
            attendance.work_duration = now - attendance.check_in
            attendance.save()
            action = "check_out"
            FaceScan.objects.create(
                id=uuid.uuid4(),
                employee_code=employee_code,
                action="check_out",
                face_confidence=result["confidence"],
                frame_image=frame_path,
                is_live=True,
            )
        else:
            action = "already_marked"

        return Response({
            "status": action,
            "employee": {
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}",
                "department": emp.department,
            },
            "action": action,
            "time": now.isoformat(),
            "confidence": result["confidence"],
            "check_in": attendance.check_in.isoformat() if attendance.check_in else None,
            "check_out": attendance.check_out.isoformat() if attendance.check_out else None,
        })


def _compute_status(company, check_in_time: datetime) -> str:
    """Determine attendance status based on company's check_in_end time."""
    check_in_local = check_in_time.astimezone().time()
    if check_in_local > company.check_in_end:
        return "late"
    return "present"


class KioskConfigView(APIView):
    """Return kiosk configuration for the company (public)."""
    permission_classes = [AllowAny]

    def get(self, request, company_code):
        company = _get_company(company_code)
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "company_code": company.company_code,
            "company_name": company.name,
            "check_in_start": str(company.check_in_start),
            "check_in_end": str(company.check_in_end),
            "work_hours": float(company.work_hours),
            "attendance_mode": company.attendance_mode,
        })
