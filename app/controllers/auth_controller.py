from flask import Blueprint, jsonify, request

from app.extensions.jwt import encode_access_token
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

user_service = UserService(UserRepository(), jwt_encode=encode_access_token)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    full_name = data.get("full_name")
    role = data.get("role", "student")

    if not username or not password:
        return jsonify({"error": "Username và password là bắt buộc"}), 400

    try:
        result = user_service.register(username, password, full_name, role)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Lỗi server"}), 500

    return (
        jsonify(
            {
                "token": result.token,
                "user": result.user.to_json(),
            }
        ),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username và password là bắt buộc"}), 400

    try:
        result = user_service.login(username, password)
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception:
        return jsonify({"error": "Lỗi server"}), 500

    return jsonify({"token": result.token, "user": result.user.to_json()}), 200

