from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "error": type(exc).__name__,
            "detail": response.data.get("detail", response.data) if isinstance(response.data, dict) else response.data,
            "status": response.status_code,
        }
        return Response(error_data, status=response.status_code)

    return response
