from platform.libs.shared.logging import get_logger
from platform.libs.shared.settings import settings

from fastapi import FastAPI, HTTPException

from modules.auth.backend.public.users import get_user_public
from modules.auth.backend.schemas.user import UserPublic

log = get_logger("auth.api")
app = FastAPI(title="auth-api", version="0.1.0")


def init_sentry(dsn: str | None) -> None:
    """Init Sentry.

    Example:
        >>> init_sentry(None)
    """
    if not dsn:
        return
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration

    sentry_sdk.init(
        dsn=dsn, integrations=[FastApiIntegration()], traces_sample_rate=0.2
    )


@app.on_event("startup")
def _startup() -> None:
    init_sentry(settings.sentry_dsn)
    log.info("auth api startup", extra={"env": settings.env})


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/users/{user_id}", response_model=UserPublic)
def get_user_route(user_id: int) -> UserPublic:
    user = get_user_public(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


def run() -> None:  # Entry point for PEX binary
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
