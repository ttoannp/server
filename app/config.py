import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # kiểm tra cho chắc
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("DATABASE_URL is not set")
