"""Sign in with Google or GitHub: the OAuth authorization-code flow, by hand.

Both views are full-page browser navigations, not API calls, so they answer with
redirects: to the provider, then back to the app ("/", or "/?auth_error=...").
"""
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from .models import SocialAccount

User = get_user_model()
TIMEOUT = 10

PROVIDERS = {
    "google": {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "scope": "openid email profile",
    },
    "github": {
        "authorize": "https://github.com/login/oauth/authorize",
        "token": "https://github.com/login/oauth/access_token",
        "scope": "read:user user:email",
    },
}


class OAuthError(Exception):
    """Carries a message that is safe to show the user."""


def credentials(provider):
    key = provider.upper()
    return getattr(settings, f"{key}_CLIENT_ID", ""), getattr(settings, f"{key}_CLIENT_SECRET", "")


def callback_url(request, provider):
    # Must match the redirect URI registered with the provider exactly. Behind
    # the Vite dev proxy the Host header is still localhost:5173, so it matches.
    return request.build_absolute_uri(reverse("oauth-callback", args=[provider]))


def back_to_app(error=None):
    return HttpResponseRedirect("/?" + urlencode({"auth_error": error}) if error else "/")


@require_GET
def start(request, provider):
    if provider not in PROVIDERS:
        raise Http404
    client_id, _ = credentials(provider)
    if not client_id:
        return back_to_app(f"{provider.title()} sign-in isn't set up on this server.")

    # Ties the callback to this browser: without it, an attacker could hand the
    # victim a callback link carrying the attacker's code (login CSRF).
    state = secrets.token_urlsafe(32)
    request.session[f"oauth_state_{provider}"] = state
    params = {
        "client_id": client_id,
        "redirect_uri": callback_url(request, provider),
        "response_type": "code",
        "scope": PROVIDERS[provider]["scope"],
        "state": state,
    }
    if provider == "google":
        params["prompt"] = "select_account"
    return HttpResponseRedirect(f"{PROVIDERS[provider]['authorize']}?{urlencode(params)}")


@require_GET
def callback(request, provider):
    if provider not in PROVIDERS:
        raise Http404

    expected = request.session.pop(f"oauth_state_{provider}", None)
    if not expected or not secrets.compare_digest(expected, request.GET.get("state", "")):
        return back_to_app("That sign-in link expired. Please try again.")
    if "code" not in request.GET:
        return back_to_app("Sign-in was cancelled.")

    try:
        token = exchange_code(request, provider, request.GET["code"])
        uid, email, name = PROFILE[provider](token)
        user = user_for(provider, uid, email, name)
    except OAuthError as e:
        return back_to_app(str(e))
    except requests.RequestException:
        return back_to_app(f"Couldn't reach {provider.title()}. Please try again.")
    if not user.is_active:
        return back_to_app("This account has been deactivated.")

    # login() rotates the session key, same as password sign-in.
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return back_to_app()


def exchange_code(request, provider, code):
    client_id, client_secret = credentials(provider)
    response = requests.post(
        PROVIDERS[provider]["token"],
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": callback_url(request, provider),
        },
        headers={"Accept": "application/json"},
        timeout=TIMEOUT,
    )
    token = response.json().get("access_token") if response.ok else None
    if not token:  # GitHub answers 200 with {"error": ...} for a bad code
        raise OAuthError(f"{provider.title()} didn't accept the sign-in. Please try again.")
    return token


def get_json(url, headers):
    response = requests.get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def google_profile(token):
    info = get_json("https://openidconnect.googleapis.com/v1/userinfo", {"Authorization": f"Bearer {token}"})
    email = info.get("email") if info.get("email_verified") else None
    return str(info["sub"]), email, info.get("name", "")


def github_profile(token):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    user = get_json("https://api.github.com/user", headers)
    emails = get_json("https://api.github.com/user/emails", headers)
    email = next((e["email"] for e in emails if e.get("primary") and e.get("verified")), None)
    return str(user["id"]), email, user.get("login", "")


PROFILE = {"google": google_profile, "github": github_profile}


def user_for(provider, uid, email, name):
    account = SocialAccount.objects.select_related("user").filter(provider=provider, uid=uid).first()
    if account:
        return account.user
    if not email:
        raise OAuthError(f"Your {provider.title()} account has no verified email address.")

    email = User.objects.normalize_email(email).lower()
    user = User.objects.filter(email__iexact=email).first()
    if user and user.has_usable_password():
        # Registration doesn't verify email, so this account may not be the
        # email's owner's. Linking would let whoever registered it (and knows
        # the password) into the real owner's sign-ins.
        raise OAuthError("An account with this email already exists. Sign in with your username and password.")

    with transaction.atomic():
        if user is None:
            # No usable password: only a provider-verified email ever created it,
            # which is what makes linking the other provider to it safe.
            user = User.objects.create_user(username=unique_username(name or email.split("@")[0]), email=email)
        SocialAccount.objects.create(provider=provider, uid=uid, user=user)
    return user


def unique_username(base):
    base = "".join(c for c in base if c.isalnum() or c in "._-")[:140] or "user"
    candidate = base
    while User.objects.filter(username__iexact=candidate).exists():
        candidate = f"{base}{secrets.randbelow(10_000)}"
    return candidate
