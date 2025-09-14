import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from services.auth.adapters.repositories.dynamodb_users import DynamoUsers

app = FastAPI(title="auth", version="0.1.0")


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def repo() -> DynamoUsers:
    return DynamoUsers.from_env()


def _jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-secret")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/register")
def register(req: RegisterRequest) -> dict:
    r = repo()
    try:
        r.create_user(req.email, req.username, req.password)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"could not create: {e}")
    return {"ok": True}


@app.post("/login")
def login(req: LoginRequest) -> dict:
    r = repo()
    rec = r.get_by_email(req.email)
    if not rec or not r.verify_password(rec, req.password):
        raise HTTPException(401, "invalid credentials")
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": rec.email,
        "name": rec.username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=12)).timestamp()),
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm="HS256")
    return {"token": token}


@app.get("/verify")
def verify(token: str) -> dict:
    try:
        data = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
        return {"valid": True, "sub": data.get("sub"), "name": data.get("name")}
    except jwt.PyJWTError as e:  # type: ignore[attr-defined]
        raise HTTPException(401, f"invalid: {e}")


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
