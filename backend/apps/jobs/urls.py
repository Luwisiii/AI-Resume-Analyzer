from django.urls import path
from .views import jobs_list

urlpatterns = [
    path("", jobs_list, name="jobs-list"), 
]
