from app.extensions.db import db
from datetime import datetime

class ExamAttempt(db.Model):
    __tablename__ = 'exam_attempts'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_score = db.Column(db.Float)

    # Dòng này giúp bạn dùng được lệnh: a.exam.title
    exam = db.relationship('Exam', backref='attempts', lazy=True) 
    
    # Relationship với User (để dùng a.student.username)
    student = db.relationship('User', backref='attempts', lazy=True)

    # Quan hệ: Một lần thi có nhiều câu trả lời
    answers = db.relationship('Answer', backref='attempt', cascade='all, delete-orphan', lazy=True)

class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('exam_attempts.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    
    # Nếu là trắc nghiệm thì lưu option_id
    selected_option_id = db.Column(db.Integer, db.ForeignKey('options.id', ondelete='SET NULL'), nullable=True)
    
    # Nếu là tự luận thì lưu text
    essay_answer = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float)