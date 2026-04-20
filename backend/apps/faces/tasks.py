import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def train_all_employees_task(self, company_code: str):
    """
    Train all approved employees in a company.
    Runs as a background Celery task.
    """
    from core.dynamic_models import get_employee_model
    from .dataset_service import get_image_paths
    from .deepface_views import _train_employee

    Employee = get_employee_model(company_code.upper())
    approved = Employee.objects.filter(image_status="approved")
    total = approved.count()

    if total == 0:
        return {"detail": "No approved employees to train.", "trained": 0}

    trained = 0
    errors = []

    for emp in approved:
        try:
            image_paths = get_image_paths(company_code, emp.employee_code)
            response = _train_employee(emp, image_paths, company_code, emp.employee_code)
            if response.status_code == 200:
                trained += 1
            else:
                errors.append(f"{emp.employee_code}: {response.data.get('detail')}")
        except Exception as e:
            errors.append(f"{emp.employee_code}: {str(e)}")
            logger.error("Training failed for %s: %s", emp.employee_code, e)

        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": trained, "total": total},
        )

    return {"trained": trained, "total": total, "errors": errors}
