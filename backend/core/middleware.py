from django.utils.deprecation import MiddlewareMixin


class AuditLogMiddleware(MiddlewareMixin):
    """Attaches request metadata to the request object for use in views/signals."""

    def process_request(self, request):
        request.audit_ip = self.get_client_ip(request)
        request.audit_user_agent = request.META.get("HTTP_USER_AGENT", "")

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
