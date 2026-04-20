from rest_framework import generics, status
from rest_framework.response import Response
from .models import Company
from .serializers import CompanySerializer, CompanyCreateSerializer
from core.permissions import IsSuperAdmin, IsCompanyManager


class CompanyListCreateView(generics.ListCreateAPIView):
    queryset = Company.objects.filter(is_active=True).order_by("name")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CompanyCreateSerializer
        return CompanySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSuperAdmin()]
        return [IsCompanyManager()]


class CompanyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    lookup_field = "company_code"

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsSuperAdmin()]
        return [IsCompanyManager()]

    def destroy(self, request, *args, **kwargs):
        company = self.get_object()
        from core.dynamic_models import drop_company_tables
        from services.vector_db import ChromaDBService
        drop_company_tables(company.company_code)
        ChromaDBService.delete_collection(company.company_code)
        company.is_active = False
        company.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
