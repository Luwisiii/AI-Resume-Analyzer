from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    path("api/resumes/", include("apps.resumes.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
]

if settings.DEBUG:
    # Dev only. In production the uploaded resumes must NOT be served as static
    # files: they are private documents behind the per-owner check in the API.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
