from django.urls import path
from .views import upload_resume, resume_detail, resume_job_match_view

urlpatterns = [
    path("upload/", upload_resume, name="resume-upload"),
    path("<int:resume_id>/", resume_detail, name="resume-detail"),
    path("<int:resume_id>/job/<int:job_id>/match/", resume_job_match_view, name="resume-job-match"),
]
