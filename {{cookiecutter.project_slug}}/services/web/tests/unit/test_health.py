from services.web.app.api.main import healthz


def test_healthz():
    assert healthz() == {"status": "ok"}
