from django.urls import path

from . import oauth
from .views import csrf, login, logout, me, register

urlpatterns = [
    path("csrf/", csrf, name="csrf"),
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),
    path("me/", me, name="me"),
    path("oauth/<str:provider>/", oauth.start, name="oauth-start"),
    path("oauth/<str:provider>/callback/", oauth.callback, name="oauth-callback"),
]
