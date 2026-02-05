from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from app.extensions.db import db


def create_app():
    app = Flask(__name__)

    # Config
    from app.config import Config

    app.config.from_object(Config)

    db.init_app(app)

    # --- Import models để Migrate nhận diện ---
    from app.models.user_model import User  # noqa: F401
    from app.models.exam_model import Exam, Question, Option  # noqa: F401
    from app.models.attempt_model import ExamAttempt, Answer  # noqa: F401

    Migrate(app, db)
    CORS(app)

    # --- Đăng ký các blueprint (controller) ---
    from app.controllers.exam_controller import exam_bp
    from app.controllers.auth_controller import auth_bp

    app.register_blueprint(exam_bp)
    app.register_blueprint(auth_bp)

    return app