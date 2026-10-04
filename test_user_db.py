from sqlalchemy import select 
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.connection import engine
from app.db.models import User

test_email = "student-test@example.com"

with Session(engine) as session:
    user=session.scalar(
        select(User).where(User.email == test_email)
    )
    if user is None:
        user = User(
            email=test_email,
            password_hash=None,
            role="student",
            is_email_verified=False,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    
    print(f"User ID:{user.id}")
    print(f"Email:{user.email}")
    print(f"Role:{user.role}")

    duplicate = User(
        email=test_email,
        password_hash=None,
        role="student",
        is_email_verified=False,
    )

    try:
        session.commit()
        raise RuntimeError("ERROR: duplicate email was accepted")
    except IntegrityError:
        session.rollback()
        print("Duplicate email correctly rejected")
