from django.urls import path
from .dataset_views import (
    CaptureImagesView, ListImagesView,
    DeleteImageView, DeleteAllImagesView, ApproveImagesView,
)
from .deepface_views import TrainEmployeeView, TrainAllView, TrainingStatusView

urlpatterns = [
    path("capture/", CaptureImagesView.as_view(), name="face-capture"),
    path("", ListImagesView.as_view(), name="face-list"),
    path("delete/", DeleteImageView.as_view(), name="face-delete"),
    path("delete-all/", DeleteAllImagesView.as_view(), name="face-delete-all"),
    path("approve/", ApproveImagesView.as_view(), name="face-approve"),
    path("train/", TrainEmployeeView.as_view(), name="face-train"),
    path("train-all/", TrainAllView.as_view(), name="face-train-all"),
    path("training-status/", TrainingStatusView.as_view(), name="face-training-status"),
]
