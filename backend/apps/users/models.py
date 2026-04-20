import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from core.models import Company


class AdminUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "superadmin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class AdminUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("superadmin", "Super Admin"),
        ("admin", "Admin"),
        ("manager", "Manager"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, null=True, blank=True, related_name="admin_users"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="admin")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    last_login_ip = models.CharField(max_length=50, blank=True)
    last_login_device = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = AdminUserManager()

    class Meta:
        db_table = "admin_users"

    def __str__(self):
        return f"{self.name} ({self.email})"

    @property
    def is_superadmin(self):
        return self.role == "superadmin"

    @property
    def is_company_admin(self):
        return self.role in ("superadmin", "admin")


class AuditLog(models.Model):
    admin_user = models.ForeignKey(
        AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.CharField(max_length=50, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} on {self.resource_type} by {self.admin_user}"


class DeviceLog(models.Model):
    EVENT_CHOICES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("error", "Error"),
        ("app_open", "App Open"),
    ]

    admin_user = models.ForeignKey(
        AdminUser, on_delete=models.CASCADE, related_name="device_logs"
    )
    device_id = models.CharField(max_length=200)
    device_model = models.CharField(max_length=200, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    event_data = models.JSONField(null=True, blank=True)
    ip_address = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "device_logs"
        ordering = ["-created_at"]
