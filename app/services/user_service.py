from dataclasses import dataclass
from typing import Optional, Tuple

from werkzeug.security import check_password_hash, generate_password_hash

from app.models.user_model import User
from app.repositories.user_repository import UserRepository


@dataclass
class AuthResult:
    user: User
    token: str


class UserService:
    """Business logic cho đăng ký / đăng nhập."""

    def __init__(self, user_repo: UserRepository, jwt_encode) -> None:
        """
        jwt_encode: hàm nhận dict payload và trả về chuỗi token (được inject từ layer khác).
        """
        self.user_repo = user_repo
        self.jwt_encode = jwt_encode

    # --- Đăng ký ---
    def register(self, username: str, password: str, full_name: Optional[str], role: str) -> AuthResult:
        if role not in ("teacher", "student"):
            raise ValueError("Role phải là 'teacher' hoặc 'student'")

        existing = self.user_repo.get_by_username(username)
        if existing:
            raise ValueError("Username đã tồn tại")

        password_hash = generate_password_hash(password)
        user = self.user_repo.create_user(username, password_hash, full_name, role)

        token = self._create_token(user)
        return AuthResult(user=user, token=token)

    # --- Đăng nhập ---
    def login(self, username: str, password: str) -> AuthResult:
        user = self.user_repo.get_by_username(username)
        if not user or not check_password_hash(user.password, password):
            raise ValueError("Sai tên đăng nhập hoặc mật khẩu")

        token = self._create_token(user)
        return AuthResult(user=user, token=token)

    # --- Helper ---
    def _create_token(self, user: User) -> str:
        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role,
        }
        return self.jwt_encode(payload)

