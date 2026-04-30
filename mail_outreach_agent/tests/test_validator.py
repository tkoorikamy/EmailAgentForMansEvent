from app.core.validator import is_valid_email, assign_statuses


def test_is_valid_email():
    assert is_valid_email("test@example.com")
    assert not is_valid_email("bad@@example")


def test_assign_statuses():
    statuses = assign_statuses(["a@test.com", "", "a@test.com", "bad"])
    assert statuses == ["duplicate", "invalid_email", "duplicate", "invalid_email"]
