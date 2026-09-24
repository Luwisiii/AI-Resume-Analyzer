from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

User = get_user_model()

PASSWORD = "s3cure-pw-here"


class AuthTests(TestCase):
    def setUp(self):
        cache.clear()  # throttle counters would otherwise leak between tests

    def register(self, client=None, **overrides):
        payload = {"username": "newuser", "email": "a@b.test", "password": PASSWORD}
        return (client or self.client).post("/api/auth/register/", {**payload, **overrides})

    def test_register_signs_the_user_in_with_an_httponly_cookie(self):
        response = self.register()
        assert response.status_code == 201
        assert "token" not in response.json()

        cookie = response.cookies["sessionid"]
        assert cookie["httponly"]

        me = self.client.get("/api/auth/me/")
        assert me.status_code == 200
        assert me.json()["username"] == "newuser"

    def test_password_is_hashed_not_stored_raw(self):
        self.register()
        user = User.objects.get(username="newuser")
        assert user.password != PASSWORD
        assert user.check_password(PASSWORD)

    def test_weak_password_is_rejected(self):
        assert self.register(password="123").status_code == 400
        assert self.register(password="newuser1").status_code == 400  # ~ username
        assert not User.objects.filter(username="newuser").exists()

    def test_duplicate_username_is_rejected(self):
        self.register()
        assert self.register(Client(), email="other@b.test").status_code == 400

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.register()
        assert self.register(Client(), username="other", email="A@B.test").status_code == 400

    def test_email_is_required(self):
        assert self.register(email="").status_code == 400

    def test_login_and_bad_credentials_get_the_same_message(self):
        User.objects.create_user("newuser", password=PASSWORD)

        ok = self.client.post("/api/auth/login/", {"username": "newuser", "password": PASSWORD})
        assert ok.status_code == 200 and ok.json()["username"] == "newuser"

        wrong_pw = Client().post("/api/auth/login/", {"username": "newuser", "password": "x"})
        no_user = Client().post("/api/auth/login/", {"username": "ghost", "password": "x"})
        assert wrong_pw.status_code == no_user.status_code == 400
        assert wrong_pw.json() == no_user.json()

    def test_logout_ends_the_session_server_side(self):
        self.register()
        stolen = self.client.cookies["sessionid"].value

        assert self.client.post("/api/auth/logout/").status_code == 204

        replay = Client()
        replay.cookies["sessionid"] = stolen
        assert replay.get("/api/auth/me/").status_code == 401

    def test_me_requires_authentication(self):
        assert self.client.get("/api/auth/me/").status_code == 401

    def test_login_is_throttled(self):
        statuses = [
            Client().post("/api/auth/login/", {"username": "x", "password": "y"}).status_code
            for _ in range(11)
        ]
        assert statuses[-1] == 429

    def test_login_requires_csrf_token(self):
        User.objects.create_user("newuser", password=PASSWORD)
        strict = Client(enforce_csrf_checks=True)
        body = {"username": "newuser", "password": PASSWORD}

        assert strict.post("/api/auth/login/", body).status_code == 403

        strict.get("/api/auth/csrf/")
        token = strict.cookies["csrftoken"].value
        assert strict.post("/api/auth/login/", body, HTTP_X_CSRFTOKEN=token).status_code == 200


def fake_response(payload, status=200):
    response = MagicMock(ok=status < 400, status_code=status)
    response.json.return_value = payload
    response.raise_for_status.side_effect = None if status < 400 else requests.HTTPError()
    return response


GITHUB_USER = {"id": 42, "login": "octo cat"}
GITHUB_EMAILS = [
    {"email": "old@b.test", "primary": False, "verified": True},
    {"email": "Octo@B.test", "primary": True, "verified": True},
]


@override_settings(GITHUB_CLIENT_ID="gh-id", GITHUB_CLIENT_SECRET="gh-secret", GOOGLE_CLIENT_ID="")
class OAuthTests(TestCase):
    def github_signin(self, client=None, user=GITHUB_USER, emails=GITHUB_EMAILS, token=None):
        client = client or self.client
        start = client.get("/api/auth/oauth/github/")
        state = parse_qs(urlparse(start["Location"]).query)["state"][0]

        token_response = fake_response(token or {"access_token": "tok"})
        with patch("apps.users.oauth.requests.post", return_value=token_response), patch(
            "apps.users.oauth.requests.get",
            side_effect=[fake_response(user), fake_response(emails)],
        ):
            return client.get("/api/auth/oauth/github/callback/", {"code": "c", "state": state})

    def test_start_redirects_to_the_provider_with_a_state(self):
        response = self.client.get("/api/auth/oauth/github/")
        assert response.status_code == 302
        query = parse_qs(urlparse(response["Location"]).query)
        assert response["Location"].startswith("https://github.com/login/oauth/authorize?")
        assert query["client_id"] == ["gh-id"]
        assert query["redirect_uri"] == ["http://testserver/api/auth/oauth/github/callback/"]
        assert len(query["state"][0]) > 30

    def test_unconfigured_provider_goes_back_with_an_error(self):
        response = self.client.get("/api/auth/oauth/google/")
        assert response["Location"].startswith("/?auth_error=")

    def test_unknown_provider_is_404(self):
        assert self.client.get("/api/auth/oauth/myspace/").status_code == 404

    def test_first_signin_creates_a_passwordless_user_and_signs_in(self):
        response = self.github_signin()
        assert response["Location"] == "/"

        user = User.objects.get(email="octo@b.test")  # primary verified, lowercased
        assert user.username == "octocat"
        assert not user.has_usable_password()
        assert self.client.get("/api/auth/me/").json()["email"] == "octo@b.test"

    def test_second_signin_reuses_the_account_even_if_the_email_changed(self):
        self.github_signin()
        emails = [{"email": "new@b.test", "primary": True, "verified": True}]
        self.github_signin(Client(), emails=emails)
        assert User.objects.count() == 1

    def test_callback_without_the_session_state_is_rejected(self):
        # A callback link planted by an attacker: this browser never started a sign-in.
        with patch("apps.users.oauth.requests.post") as post:
            response = self.client.get("/api/auth/oauth/github/callback/", {"code": "c", "state": "x"})
        assert "auth_error" in response["Location"]
        post.assert_not_called()
        assert self.client.get("/api/auth/me/").status_code == 401

    def test_does_not_take_over_a_password_account_with_the_same_email(self):
        User.objects.create_user("owner", email="octo@b.test", password=PASSWORD)
        response = self.github_signin()
        assert "auth_error" in response["Location"]
        assert not User.objects.get(username="owner").social_accounts.exists()

    def test_unverified_email_is_refused(self):
        emails = [{"email": "octo@b.test", "primary": True, "verified": False}]
        assert "auth_error" in self.github_signin(emails=emails)["Location"]
        assert not User.objects.filter(email="octo@b.test").exists()

    def test_rejected_code_is_an_error_not_a_crash(self):
        response = self.github_signin(token={"error": "bad_verification_code"})
        assert "auth_error" in response["Location"]

    def test_username_collision_gets_a_suffix(self):
        User.objects.create_user("octocat", email="someone@else.test", password=PASSWORD)
        self.github_signin()
        assert User.objects.get(email="octo@b.test").username.startswith("octocat")
        assert User.objects.filter(username__istartswith="octocat").count() == 2
