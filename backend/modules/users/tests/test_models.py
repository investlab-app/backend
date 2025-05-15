import pytest
from modules.users.models import User

pytestmark = pytest.mark.django_db


def test_user_creation(user):
    assert isinstance(user, User)
    assert user.pk is not None
