import uuid
from django.db import models


class Company(models.Model):
    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
        ("business", "Business"),
    ]
    ATTENDANCE_MODE_CHOICES = [
        ("daily", "Daily"),
        ("continuous", "Continuous"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to="company_logos/", null=True, blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")
    max_employees = models.IntegerField(default=100)
    check_in_start = models.TimeField(default="09:00")
    check_in_end = models.TimeField(default="10:00")
    work_hours = models.DecimalField(max_digits=4, decimal_places=1, default=8.0)
    attendance_mode = models.CharField(
        max_length=20, choices=ATTENDANCE_MODE_CHOICES, default="daily"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "companies"
        verbose_name_plural = "Companies"

    def __str__(self):
        return f"{self.name} ({self.company_code})"
