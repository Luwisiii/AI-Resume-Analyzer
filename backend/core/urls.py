from django.contrib import admin
from django.urls import path, include


# Uploaded resumes are deliberately NOT served from MEDIA_URL, not even in DEBUG:
# they are private documents, reachable only through the per-owner API.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    path("api/resumes/", include("apps.resumes.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
]
