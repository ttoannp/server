from app.extensions.db import db
from datetime import datetime

class Exam(db.Model):
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer, nullable=False) # Phút
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ: Một đề thi có nhiều câu hỏi
    # cascade='all, delete-orphan': Xóa đề là xóa luôn câu hỏi
    questions = db.relationship('Question', backref='exam', cascade='all, delete-orphan', lazy=True)

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(10), nullable=False) # 'mcq', 'essay'
    score = db.Column(db.Float, default=1.0)

    # Quan hệ: Một câu hỏi có nhiều đáp án chọn (Option)
    options = db.relationship('Option', backref='question', cascade='all, delete-orphan', lazy=True)

class Option(db.Model):
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)