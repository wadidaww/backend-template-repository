from __future__ import annotations

import factory
from factory import LazyFunction

from app.core.security import get_password_hash
from app.models.user import User


class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    hashed_password = LazyFunction(lambda: get_password_hash("Password123!"))
    full_name = factory.Faker("name")
    is_active = True
    is_superuser = False
