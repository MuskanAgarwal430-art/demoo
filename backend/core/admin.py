from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "company_code", "plan", "max_employees", "is_active", "created_at"]
    list_filter = ["plan", "is_active"]
    search_fields = ["name", "company_code"]
    readonly_fields = ["id", "created_at"]
