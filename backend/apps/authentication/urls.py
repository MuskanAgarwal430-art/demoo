from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import login, logout, verify_token

urlpatterns = [
    path("login/", login, name="auth-login"),
    path("logout/", logout, name="auth-logout"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("verify-token/", verify_token, name="auth-verify"),
]
