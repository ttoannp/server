# backend/app/repositories/exam_repository.py
from app.models.exam_model import Exam, Question, Option
from app.extensions.db import db

class ExamRepository:
    def create_full_exam(self, data, created_by=None):
        try:
            # 1. Tạo Exam
            new_exam = Exam(
                title=data['title'],
                description=data.get('description', ''),
                duration=int(data['duration']),
                created_by=created_by
            )
            db.session.add(new_exam)
            db.session.flush() # Để lấy ID của exam vừa tạo

            # 2. Duyệt qua danh sách câu hỏi
            for q_data in data.get('questions', []):
                new_question = Question(
                    exam_id=new_exam.id,
                    content=q_data['content'],
                    question_type=q_data.get('question_type', 'mcq'),
                    score=float(q_data.get('score', 1.0))
                )
                db.session.add(new_question)
                db.session.flush() # Để lấy ID của question vừa tạo

                # 3. Duyệt qua danh sách đáp án (nếu là trắc nghiệm)
                if new_question.question_type == 'mcq':
                    for opt_data in q_data.get('options', []):
                        new_option = Option(
                            question_id=new_question.id,
                            content=opt_data['content'],
                            is_correct=opt_data.get('is_correct', False)
                        )
                        db.session.add(new_option)

            # 4. Lưu tất cả vào DB
            db.session.commit()
            return new_exam
        except Exception as e:
            db.session.rollback() # Nếu lỗi thì hủy hết, không lưu dở dang
            raise e