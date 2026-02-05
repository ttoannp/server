from app.extensions.db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # Lưu hash nhé
    full_name = db.Column(db.String(150))
    role = db.Column(db.String(20), nullable=False) # 'teacher' hoặc 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ: Một user có thể tạo nhiều bài thi (nếu là teacher)
    exams_created = db.relationship('Exam', backref='creator', lazy=True)
    
    

    def to_json(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role
        }