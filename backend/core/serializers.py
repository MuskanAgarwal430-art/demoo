from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class CompanyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "company_code", "name", "email", "phone", "address",
            "plan", "max_employees", "check_in_start", "check_in_end",
            "work_hours", "attendance_mode",
        ]

    def validate_company_code(self, value):
        # Only alphanumeric + underscore, uppercase
        import re
        code = value.upper().strip()
        if not re.match(r"^[A-Z0-9_]+$", code):
            raise serializers.ValidationError(
                "company_code must contain only letters, numbers, and underscores."
            )
        return code

    def create(self, validated_data):
        validated_data["company_code"] = validated_data["company_code"].upper()
        company = Company.objects.create(**validated_data)
        # Provision per-company MySQL tables + ChromaDB collection
        from core.dynamic_models import provision_company_tables
        from services.vector_db import ChromaDBService
        provision_company_tables(company.company_code)
        ChromaDBService.get_collection(company.company_code)
        return company
