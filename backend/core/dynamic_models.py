import uuid
from django.db import models, connection

# Cache to avoid re-creating model classes on every call
_model_cache: dict = {}


def _table_exists(table_name: str) -> bool:
    return table_name in connection.introspection.table_names()


# ---------------------------------------------------------------------------
# Model builders
# ---------------------------------------------------------------------------

def get_employee_model(company_code: str):
    key = f"{company_code}__employees"
    if key in _model_cache:
        return _model_cache[key]

    table_name = f"company_{company_code}_employees"

    attrs = {
        "__module__": __name__,
        "Meta": type("Meta", (), {
            "db_table": table_name,
            "app_label": "core",
        }),
        "id": models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
        "employee_code": models.CharField(max_length=50, unique=True),
        "first_name": models.CharField(max_length=100),
        "last_name": models.CharField(max_length=100),
        "email": models.EmailField(blank=True),
        "phone": models.CharField(max_length=20, blank=True),
        "department": models.CharField(max_length=100, blank=True),
        "designation": models.CharField(max_length=100, blank=True),
        "role": models.CharField(
            max_length=20,
            choices=[("staff", "Staff"), ("manager", "Manager")],
            default="staff",
        ),
        "status": models.CharField(
            max_length=20,
            choices=[
                ("active", "Active"),
                ("inactive", "Inactive"),
                ("terminated", "Terminated"),
            ],
            default="active",
        ),
        # Face enrollment
        "face_enrolled": models.BooleanField(default=False),
        "chromadb_id": models.CharField(max_length=100, blank=True),
        "image_count": models.IntegerField(default=0),
        "image_status": models.CharField(
            max_length=20,
            choices=[
                ("pending", "Pending"),
                ("captured", "Captured"),
                ("approved", "Approved"),
                ("trained", "Trained"),
            ],
            default="pending",
        ),
        "enrolled_at": models.DateTimeField(null=True, blank=True),
        "created_at": models.DateTimeField(auto_now_add=True),
        "updated_at": models.DateTimeField(auto_now=True),
    }

    model_class = type(f"{company_code}Employee", (models.Model,), attrs)
    _model_cache[key] = model_class
    return model_class


def get_attendance_model(company_code: str):
    key = f"{company_code}__attendance"
    if key in _model_cache:
        return _model_cache[key]

    table_name = f"company_{company_code}_attendance"

    attrs = {
        "__module__": __name__,
        "Meta": type("Meta", (), {
            "db_table": table_name,
            "app_label": "core",
            "unique_together": [("employee_code", "date")],
        }),
        "id": models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
        "employee_code": models.CharField(max_length=50, db_index=True),
        "date": models.DateField(db_index=True),
        "check_in": models.DateTimeField(null=True, blank=True),
        "check_out": models.DateTimeField(null=True, blank=True),
        "work_duration": models.DurationField(null=True, blank=True),
        "status": models.CharField(
            max_length=20,
            choices=[
                ("present", "Present"),
                ("late", "Late"),
                ("half_day", "Half Day"),
                ("absent", "Absent"),
            ],
            default="present",
        ),
        "check_in_confidence": models.FloatField(null=True, blank=True),
        "check_out_confidence": models.FloatField(null=True, blank=True),
        "notes": models.TextField(blank=True),
        "created_at": models.DateTimeField(auto_now_add=True),
    }

    model_class = type(f"{company_code}Attendance", (models.Model,), attrs)
    _model_cache[key] = model_class
    return model_class


def get_face_scan_model(company_code: str):
    key = f"{company_code}__face_scans"
    if key in _model_cache:
        return _model_cache[key]

    table_name = f"company_{company_code}_face_scans"

    attrs = {
        "__module__": __name__,
        "Meta": type("Meta", (), {
            "db_table": table_name,
            "app_label": "core",
        }),
        "id": models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
        "employee_code": models.CharField(max_length=50, blank=True, db_index=True),
        "timestamp": models.DateTimeField(auto_now_add=True),
        "action": models.CharField(
            max_length=20,
            choices=[
                ("check_in", "Check In"),
                ("check_out", "Check Out"),
                ("unrecognized", "Unrecognized"),
            ],
        ),
        "face_confidence": models.FloatField(default=0.0),
        "frame_image": models.ImageField(
            upload_to=f"detections/{company_code}/", null=True, blank=True
        ),
        "is_live": models.BooleanField(default=True),
        "created_at": models.DateTimeField(auto_now_add=True),
    }

    model_class = type(f"{company_code}FaceScan", (models.Model,), attrs)
    _model_cache[key] = model_class
    return model_class


# ---------------------------------------------------------------------------
# Table provisioning
# ---------------------------------------------------------------------------

def get_all_company_models(company_code: str):
    return [
        get_employee_model(company_code),
        get_attendance_model(company_code),
        get_face_scan_model(company_code),
    ]


def provision_company_tables(company_code: str):
    """
    Creates all per-company MySQL tables.
    Called once when a new company is onboarded.
    """
    with connection.schema_editor() as editor:
        for model in get_all_company_models(company_code):
            if not _table_exists(model._meta.db_table):
                editor.create_model(model)


def drop_company_tables(company_code: str):
    """
    Drops all per-company tables.
    Called when a company is permanently deleted.
    """
    with connection.schema_editor() as editor:
        for model in reversed(get_all_company_models(company_code)):
            if _table_exists(model._meta.db_table):
                editor.delete_model(model)
    # Remove from cache
    for key in list(_model_cache.keys()):
        if key.startswith(f"{company_code}__"):
            del _model_cache[key]
