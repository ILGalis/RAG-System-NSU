import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.connection import engine
from app.models import User


def test_user_creation_and_unique_email():
    test_email = "student-test@example.com"
    test_password_hash = "$argon2id$v=19$m=65536,t=3,p=4$fakehashfor test"

    with Session(engine) as session:
        user = session.scalar(
            select(User).where(User.email == test_email)
        )

        if user is None:
            user = User(
                email=test_email,
                password_hash=test_password_hash,
                role="student",
                is_email_verified=False,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        assert user.email == test_email
        assert user.role == "student"

        duplicate = User(
            email=test_email,
            password_hash=test_password_hash,
            role="student",
            is_email_verified=False,
        )
        session.add(duplicate)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()