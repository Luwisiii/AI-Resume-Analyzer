from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class AuthTests(TestCase):
    def register(self, **overrides):
        payload = {"username": "newuser", "email": "a@b.test", "password": "s3cure-pw-here"}
        return self.client.post("/api/auth/register/", {**payload, **overrides})

    def test_register_returns_a_usable_token(self):
        response = self.register()
        assert response.status_code == 201

        token = response.json()["token"]
        me = self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Token {token}")
        assert me.status_code == 200
        assert me.json()["username"] == "newuser"

    def test_password_is_hashed_not_stored_raw(self):
        self.register()
        user = User.objects.get(username="newuser")
        assert user.password != "s3cure-pw-here"
        assert user.check_password("s3cure-pw-here")

    def test_weak_password_is_rejected(self):
        assert self.register(password="123").status_code == 400
        assert not User.objects.filter(username="newuser").exists()

    def test_duplicate_username_is_rejected(self):
        self.register()
        assert self.register(email="other@b.test").status_code == 400

    def test_login_returns_a_token_and_bad_credentials_do_not(self):
        self.register()

        ok = self.client.post(
            "/api/auth/login/", {"username": "newuser", "password": "s3cure-pw-here"}
        )
        assert ok.status_code == 200 and ok.json()["token"]

        bad = self.client.post(
            "/api/auth/login/", {"username": "newuser", "password": "wrong"}
        )
        assert bad.status_code == 400

    def test_me_requires_authentication(self):
        assert self.client.get("/api/auth/me/").status_code == 401
