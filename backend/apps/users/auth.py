from rest_framework import authentication


class SessionAuthentication(authentication.SessionAuthentication):
    """DRF's session auth answers a missing login with 403. Naming a scheme makes
    it 401, so the client can tell "sign in again" from "not allowed"."""

    def authenticate_header(self, request):
        return "Session"
