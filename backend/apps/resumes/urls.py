from django.urls import path
from .views import upload_resume, resume_detail

urlpatterns = [
    path("upload/", upload_resume, name="resume-upload"),
    path("<int:resume_id>/", resume_detail, name="resume-detail"),
]
