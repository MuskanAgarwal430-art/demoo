from django.urls import path
from .employee_views import EmployeeListCreateView, EmployeeDetailView
from .kiosk_views import KioskRecognizeView, KioskConfigView
from .attendance_views import AttendanceListView, AttendanceSummaryView, AttendanceExportView

urlpatterns = [
    # Employees
    path("employees/", EmployeeListCreateView.as_view(), name="employee-list"),
    path("employees/<str:employee_code>/", EmployeeDetailView.as_view(), name="employee-detail"),

    # Kiosk (public)
    path("kiosk/recognize/", KioskRecognizeView.as_view(), name="kiosk-recognize"),
    path("kiosk/config/", KioskConfigView.as_view(), name="kiosk-config"),

    # Attendance
    path("attendance/", AttendanceListView.as_view(), name="attendance-list"),
    path("attendance/summary/", AttendanceSummaryView.as_view(), name="attendance-summary"),
    path("attendance/export/", AttendanceExportView.as_view(), name="attendance-export"),
]
