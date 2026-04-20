from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "superadmin")


class IsCompanyAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("superadmin", "admin")
        )


class IsCompanyManager(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("superadmin", "admin", "manager")
        )


class BelongsToCompany(BasePermission):
    """Ensures the admin user belongs to the company in the URL."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == "superadmin":
            return True
        company_code = view.kwargs.get("company_code")
        return (
            request.user.company is not None
            and request.user.company.company_code == company_code
        )
