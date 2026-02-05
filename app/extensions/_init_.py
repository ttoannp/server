from flask import Flask
from app.config import Config
from app.extensions.db import db

def create_app():
    app = Flask(__name__)

    # load config
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)

    # test connection khi app start
    with app.app_context():
        from sqlalchemy import text
        db.session.execute(text("SELECT 1"))

    # register routes
    from app.routes.health import health_bp
    app.register_blueprint(health_bp)

    return app
