import os
from datetime import datetime, timedelta, timezone
from typing import Dict

import jwt
from flask import current_app


def _get_secret_key() -> str:
    # Ưu tiên config trong Flask, fallback về biến môi trường
    secret = getattr(current_app, "config", {}).get("JWT_SECRET_KEY") if current_app else None
    return secret or os.getenv("JWT_SECRET_KEY", "change-me-in-production")


def encode_access_token(payload: Dict, expires_minutes: int = 60) -> str:
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)
    to_encode.update(
        {
            "iat": now,
            "exp": now + timedelta(minutes=expires_minutes),
        }
    )
    secret_key = _get_secret_key()
    return jwt.encode(to_encode, secret_key, algorithm="HS256")

