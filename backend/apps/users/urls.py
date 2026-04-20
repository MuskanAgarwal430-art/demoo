from django.urls import path
from .views import MeView, change_password

urlpatterns = [
    path("me/", MeView.as_view(), name="user-me"),
    path("change-password/", change_password, name="change-password"),
]
