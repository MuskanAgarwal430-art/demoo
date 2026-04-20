import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from core.dynamic_models import get_employee_model
from core.models import Company
from core.permissions import IsCompanyManager, BelongsToCompany


def get_company_or_404(company_code):
    try:
        return Company.objects.get(company_code=company_code.upper(), is_active=True)
    except Company.DoesNotExist:
        return None


def employee_to_dict(emp):
    return {
        "id": str(emp.id),
        "employee_code": emp.employee_code,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "full_name": f"{emp.first_name} {emp.last_name}",
        "email": emp.email,
        "phone": emp.phone,
        "department": emp.department,
        "designation": emp.designation,
        "role": emp.role,
        "status": emp.status,
        "face_enrolled": emp.face_enrolled,
        "image_count": emp.image_count,
        "image_status": emp.image_status,
        "enrolled_at": emp.enrolled_at,
        "created_at": emp.created_at,
        "updated_at": emp.updated_at,
    }


class EmployeeListCreateView(APIView):
    permission_classes = [IsCompanyManager, BelongsToCompany]

    def get(self, request, company_code):
        company = get_company_or_404(company_code)
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

        Employee = get_employee_model(company_code.upper())
        employees = Employee.objects.all().order_by("first_name")

        # Filters
        emp_status = request.query_params.get("status")
        department = request.query_params.get("department")
        search = request.query_params.get("search")
        face_enrolled = request.query_params.get("face_enrolled")

        if emp_status:
            employees = employees.filter(status=emp_status)
        if department:
            employees = employees.filter(department__icontains=department)
        if search:
            from django.db.models import Q
            employees = employees.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(employee_code__icontains=search)
                | Q(email__icontains=search)
            )
        if face_enrolled is not None:
            employees = employees.filter(face_enrolled=face_enrolled.lower() == "true")

        return Response([employee_to_dict(e) for e in employees])

    def post(self, request, company_code):
        company = get_company_or_404(company_code)
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

        Employee = get_employee_model(company_code.upper())

        data = request.data
        required = ["employee_code", "first_name", "last_name"]
        for field in required:
            if not data.get(field):
                return Response(
                    {"detail": f"{field} is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if Employee.objects.filter(employee_code=data["employee_code"]).exists():
            return Response(
                {"detail": "Employee with this code already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        # Check max_employees limit
        if Employee.objects.count() >= company.max_employees:
            return Response(
                {"detail": f"Employee limit ({company.max_employees}) reached."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        emp = Employee.objects.create(
            id=uuid.uuid4(),
            employee_code=data["employee_code"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            department=data.get("department", ""),
            designation=data.get("designation", ""),
            role=data.get("role", "staff"),
            status=data.get("status", "active"),
        )
        return Response(employee_to_dict(emp), status=status.HTTP_201_CREATED)


class EmployeeDetailView(APIView):
    permission_classes = [IsCompanyManager, BelongsToCompany]

    def get(self, request, company_code, employee_code):
        Employee = get_employee_model(company_code.upper())
        try:
            emp = Employee.objects.get(employee_code=employee_code)
        except Employee.DoesNotExist:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(employee_to_dict(emp))

    def put(self, request, company_code, employee_code):
        Employee = get_employee_model(company_code.upper())
        try:
            emp = Employee.objects.get(employee_code=employee_code)
        except Employee.DoesNotExist:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        updatable = ["first_name", "last_name", "email", "phone", "department", "designation", "role", "status"]
        for field in updatable:
            if field in data:
                setattr(emp, field, data[field])
        emp.save()
        return Response(employee_to_dict(emp))

    def delete(self, request, company_code, employee_code):
        Employee = get_employee_model(company_code.upper())
        try:
            emp = Employee.objects.get(employee_code=employee_code)
        except Employee.DoesNotExist:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
        emp.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
