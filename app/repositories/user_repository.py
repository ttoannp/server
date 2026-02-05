from typing import Optional

from app.extensions.db import db
from app.models.user_model import User


class UserRepository:
    """DAO layer cho bảng users."""

    def get_by_username(self, username: str) -> Optional[User]:
        return User.query.filter_by(username=username).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return User.query.get(user_id)

    def create_user(self, username: str, password_hash: str, full_name: str | None, role: str) -> User:
        user = User(
            username=username,
            password=password_hash,
            full_name=full_name,
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        return user

