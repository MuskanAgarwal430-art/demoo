import uuid
import logging
from datetime import date

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def mark_daily_absences():
    """
    Runs at 23:50 every day.
    For each active company, find active employees with no attendance record today
    and create an 'absent' record.
    """
    from core.models import Company
    from core.dynamic_models import get_employee_model, get_attendance_model

    today = date.today()
    companies = Company.objects.filter(is_active=True)

    total_marked = 0
    for company in companies:
        try:
            Employee = get_employee_model(company.company_code)
            Attendance = get_attendance_model(company.company_code)

            active_employees = Employee.objects.filter(status="active")
            already_marked = set(
                Attendance.objects.filter(date=today).values_list("employee_code", flat=True)
            )

            absent_records = []
            for emp in active_employees:
                if emp.employee_code not in already_marked:
                    absent_records.append(
                        Attendance(
                            id=uuid.uuid4(),
                            employee_code=emp.employee_code,
                            date=today,
                            status="absent",
                        )
                    )

            if absent_records:
                Attendance.objects.bulk_create(absent_records)
                total_marked += len(absent_records)
                logger.info("Marked %d absent for company %s", len(absent_records), company.company_code)

        except Exception as e:
            logger.error("mark_daily_absences failed for %s: %s", company.company_code, e)

    return f"Marked {total_marked} absences across all companies."
