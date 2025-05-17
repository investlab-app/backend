import pytest

from modules.users.models import User


@pytest.fixture
def user():
    return User.objects.create_user( # type: ignore
        email="test@example.com",
        password="test-password",
        first_name="Test",
        last_name="User",
    )
