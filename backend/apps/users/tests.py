from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

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
