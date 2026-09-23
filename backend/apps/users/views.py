from django.contrib.auth import authenticate, login as start_session, logout as end_session
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle

from .auth import SessionAuthentication
from .serializers import LoginSerializer, RegisterSerializer


class AuthThrottle(SimpleRateThrottle):
    """Per client IP, signed in or not."""

    scope = "auth"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


def require_csrf(request):
    # DRF only checks CSRF for already-authenticated sessions. Login and register
    # are anonymous, so check explicitly — otherwise a hostile page can sign the
    # victim into an attacker's account (login CSRF).
    SessionAuthentication().enforce_csrf(request)


def profile(user):
    return {"username": user.username, "email": user.email}


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    """Sets the csrftoken cookie the client must echo back on every write."""
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def register(request):
    require_csrf(request)
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    start_session(request, user)
    return Response(profile(user), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def login(request):
    require_csrf(request)
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = authenticate(request, **serializer.validated_data)
    if user is None:
        # One message for unknown user and wrong password: no account enumeration.
        return Response(
            {"detail": "Incorrect username or password."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # login() rotates the session key, so a pre-planted session id is worthless.
    start_session(request, user)
    return Response(profile(user))


@api_view(["POST"])
def logout(request):
    end_session(request)  # flushes the session server-side, not just the cookie
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def me(request):
    return Response(profile(request.user))
