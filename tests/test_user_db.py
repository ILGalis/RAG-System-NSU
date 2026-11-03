import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from tests.conftest import TestingSessionLocal
from backend.models import User


def test_user_creation_and_unique_email():
    test_email = "student-test@g.nsu.ru"
    test_password_hash = "$argon2id$v=19$m=65536,t=3,p=4$fakehashfor test"

    with TestingSessionLocal() as session:
        user = session.scalar(select(User).where(User.email == test_email))

        if user is None:
            user = User(
                email=test_email,
                first_name="Student",
                last_name="Test",
                password_hash=test_password_hash,
                role="student",
                is_email_verified=False,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        assert user.email == test_email
        assert user.role == "student"
        assert user.first_name == "Student"
        assert user.last_name == "Test"

        duplicate = User(
            email=test_email,
            first_name="Dup",
            last_name="User",
            password_hash=test_password_hash,
            role="student",
            is_email_verified=False,
        )
        session.add(duplicate)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()