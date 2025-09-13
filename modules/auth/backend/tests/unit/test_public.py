from modules.auth.backend.public.users import get_user_public


def test_get_user_public_present():
    u = get_user_public(1)
    assert u is not None and u.id == 1


def test_get_user_public_absent():
    assert get_user_public(9999) is None
