from fastapi.testclient import TestClient

from services.auth.app.api.main import app


class FakeUser:
    def __init__(self, email: str, username: str, password_hash: str, salt: str):
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.salt = salt


class FakeRepo:
    def __init__(self):
        self.users: dict[str, FakeUser] = {}

    def create_user(self, email: str, username: str, password: str):
        # store password in plain form for simplicity in tests
        self.users[email] = FakeUser(email, username, password_hash=password, salt="s")

    def get_by_email(self, email: str):
        return self.users.get(email)

    def verify_password(self, rec: FakeUser, password: str) -> bool:
        return rec.password_hash == password


def test_register_and_login(monkeypatch):
    import services.auth.app.api.main as mod

    repo = FakeRepo()
    monkeypatch.setattr(mod, "repo", lambda: repo)
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    client = TestClient(app)

    r = client.post(
        "/register", json={"email": "a@b.com", "username": "u", "password": "p"}
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    login = client.post("/login", json={"email": "a@b.com", "password": "p"})
    assert login.status_code == 200
    token = login.json().get("token")
    assert token and isinstance(token, str)

    v = client.get("/verify", params={"token": token})
    assert v.status_code == 200
    body = v.json()
    assert body.get("valid") is True
    assert body.get("sub") == "a@b.com"
