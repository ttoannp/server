# backend/app/controllers/exam_controller.py
from flask import Blueprint, jsonify, request

from app.extensions.db import db
from app.models.attempt_model import Answer, ExamAttempt
from app.models.exam_model import Exam, Option, Question
from app.models.user_model import User
from app.repositories.exam_repository import ExamRepository
from app.services.exam_pdf_service import ExamPdfParser

exam_bp = Blueprint("exam", __name__, url_prefix="/api/exams")
exam_repo = ExamRepository()


@exam_bp.route("", methods=["GET"])
def list_exams():
    exams = Exam.query.all()
    return jsonify(
        [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "duration": e.duration,
            }
            for e in exams
        ]
    )


@exam_bp.route("/<int:exam_id>", methods=["GET"])
def get_exam(exam_id: int):
    exam = Exam.query.get_or_404(exam_id)

    return jsonify(
        {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "duration": exam.duration,
            "questions": [
                {
                    "id": q.id,
                    "content": q.content,
                    "question_type": q.question_type,
                    "score": q.score,
                    "options": [
                        {
                            "id": o.id,
                            "content": o.content,
                            # Không trả field is_correct ra UI để tránh lộ đáp án
                        }
                        for o in q.options
                    ]
                    if q.question_type == "mcq"
                    else [],
                }
                for q in exam.questions
            ],
        }
    )


@exam_bp.route("/create", methods=["POST"])
def create_exam():
    data = request.get_json() or {}
    created_by = data.get("created_by")  # user_id của người tạo

    if not data.get("title") or not data.get("questions"):
        return jsonify({"error": "Tiêu đề và câu hỏi không được để trống"}), 400

    try:
        new_exam = exam_repo.create_full_exam(data, created_by=created_by)
        return (
            jsonify(
                {
                    "message": "Tạo đề thi thành công!",
                    "exam_id": new_exam.id,
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"error": "Lỗi Server", "details": str(e)}), 500


@exam_bp.route("/<int:exam_id>/start", methods=["POST"])
def start_exam(exam_id: int):
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id là bắt buộc để bắt đầu làm bài"}), 400

    exam = Exam.query.get_or_404(exam_id)
    
    # Kiểm tra xem đã có attempt chưa hoàn thành chưa (chưa có end_time)
    existing_attempt = ExamAttempt.query.filter_by(
        exam_id=exam.id,
        user_id=user_id,
        end_time=None
    ).first()
    
    if existing_attempt:
        # Trả về attempt đã có thay vì tạo mới
        return jsonify({"attempt_id": existing_attempt.id}), 200
    
    attempt = ExamAttempt(exam_id=exam.id, user_id=user_id)
    db.session.add(attempt)
    db.session.commit()

    return jsonify({"attempt_id": attempt.id}), 201


@exam_bp.route("/<int:exam_id>/submit", methods=["POST"])
def submit_exam(exam_id: int):
    data = request.get_json() or {}
    attempt_id = data.get("attempt_id")
    answers_payload = data.get("answers", [])

    attempt = ExamAttempt.query.get_or_404(attempt_id)
    if attempt.exam_id != exam_id:
        return jsonify({"error": "attempt_id không thuộc exam này"}), 400

    total_score = 0.0

    for ans in answers_payload:
        question_id = ans.get("question_id")
        selected_option_id = ans.get("selected_option_id")
        essay_answer = ans.get("essay_answer")

        if not question_id:
            continue

        question = Question.query.get(question_id)
        if not question:
            continue

        score = 0.0

        if question.question_type == "mcq" and selected_option_id:
            option = Option.query.get(selected_option_id)
            if option and option.is_correct:
                score = question.score

        if question.question_type == "essay":
            # Tạm thời chưa chấm tự luận, để 0 hoặc sau này chấm tay
            score = 0.0

        answer = Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=selected_option_id,
            essay_answer=essay_answer,
            score=score,
        )
        db.session.add(answer)
        total_score += score

    attempt.total_score = total_score
    from datetime import datetime
    attempt.end_time = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Nộp bài thành công", "total_score": total_score}), 200


# ... (Các import giữ nguyên)

@exam_bp.route("/parse-pdf", methods=["POST"])
def parse_exam_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Vui lòng chọn file PDF"}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Không có file được upload"}), 400
        
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Chỉ hỗ trợ file PDF"}), 400

    try:
        # pdfplumber yêu cầu một file-like object thực thụ
        # request.files['file'] hoạt động tốt, nhưng để chắc chắn ta không cần seek(0) ở đây
        # vì flask đã handle việc đó rồi.
        
        parser = ExamPdfParser()
        
        # Truyền trực tiếp stream vào parser
        questions = parser.parse_file(file)
        
        if not questions:
            return jsonify({
                "error": "Không nhận diện được câu hỏi nào. Vui lòng kiểm tra định dạng file.",
                "hint": "Hỗ trợ định dạng: 'Câu 1:', '1.', 'Bài 1' và đáp án 'A.', 'B.', 'C.', 'D.'"
            }), 400
            
        return jsonify({
            "message": "Đọc file thành công",
            "questions": questions,
            "count": len(questions)
        }), 200
        
    except Exception as e:
        print(f"Server Error Parse PDF: {str(e)}") # Log lỗi ra terminal để debug
        return jsonify({
            "error": "Lỗi khi xử lý file PDF", 
            "details": str(e)
        }), 500


@exam_bp.route("/<int:exam_id>", methods=["DELETE"])
def delete_exam(exam_id: int):
    """Xóa đề thi. Chỉ giáo viên tạo đề mới được xóa."""
    data = request.get_json() or {}
    user_id = data.get("user_id") or request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id là bắt buộc"}), 400

    exam = Exam.query.get_or_404(exam_id)
    if exam.created_by != user_id:
        return jsonify({"error": "Bạn không có quyền xóa đề này"}), 403

    try:
        db.session.delete(exam)
        db.session.commit()
        return jsonify({"message": "Đã xóa đề thi thành công"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Lỗi khi xóa đề thi", "details": str(e)}), 500


@exam_bp.route("/my-created", methods=["GET"])
def get_my_created_exams():
    """Lấy danh sách đề mà giáo viên đã tạo."""
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id là bắt buộc"}), 400

    exams = Exam.query.filter_by(created_by=user_id).order_by(Exam.created_at.desc()).all()
    return jsonify(
        [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "duration": e.duration,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in exams
        ]
    )


@exam_bp.route("/my-attempts", methods=["GET"])
def get_my_attempts():
    """Lấy danh sách đề mà user đã làm."""
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id là bắt buộc"}), 400

    attempts = (
        ExamAttempt.query.filter_by(user_id=user_id)
        .order_by(ExamAttempt.start_time.desc())
        .all()
    )
    return jsonify(
        [
            {
                "attempt_id": a.id,
                "exam_id": a.exam_id,
                "exam_title": a.exam.title if a.exam else None,
                "total_score": a.total_score,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "end_time": a.end_time.isoformat() if a.end_time else None,
            }
            for a in attempts
        ]
    )


@exam_bp.route("/<int:exam_id>/detail", methods=["GET"])
def get_exam_detail_with_answers(exam_id: int):
    """Lấy chi tiết đề với đáp án đúng (chỉ dành cho giáo viên tạo đề)."""
    user_id = request.args.get("user_id", type=int)

    exam = Exam.query.get_or_404(exam_id)
    if exam.created_by != user_id:
        return jsonify({"error": "Bạn không có quyền xem đề này"}), 403

    return jsonify(
        {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "duration": exam.duration,
            "questions": [
                {
                    "id": q.id,
                    "content": q.content,
                    "question_type": q.question_type,
                    "score": q.score,
                    "options": [
                        {
                            "id": o.id,
                            "content": o.content,
                            "is_correct": o.is_correct,
                        }
                        for o in q.options
                    ]
                    if q.question_type == "mcq"
                    else [],
                }
                for q in exam.questions
            ],
        }
    )


@exam_bp.route("/<int:exam_id>/attempts", methods=["GET"])
def get_exam_attempts(exam_id: int):
    """Lấy danh sách bài làm của học sinh cho một đề (chỉ giáo viên tạo đề)."""
    user_id = request.args.get("user_id", type=int)

    exam = Exam.query.get_or_404(exam_id)
    if exam.created_by != user_id:
        return jsonify({"error": "Bạn không có quyền xem bài làm này"}), 403

    attempts = (
        ExamAttempt.query.filter_by(exam_id=exam_id)
        .order_by(ExamAttempt.start_time.desc())
        .all()
    )

    return jsonify(
        [
            {
                "attempt_id": a.id,
                "student_id": a.user_id,
                "student_name": a.student.username if a.student else None,
                "total_score": a.total_score,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "end_time": a.end_time.isoformat() if a.end_time else None,
                "answers": [
                    {
                        "question_id": ans.question_id,
                        "selected_option_id": ans.selected_option_id,
                        "essay_answer": ans.essay_answer,
                        "score": ans.score,
                    }
                    for ans in a.answers
                ],
            }
            for a in attempts
        ]
    )


@exam_bp.route("/attempts/<int:attempt_id>/grade", methods=["POST"])
def grade_essay_answer(attempt_id: int):
    """Chấm điểm cho câu tự luận."""
    data = request.get_json() or {}
    question_id = data.get("question_id")
    score = data.get("score")

    if question_id is None or score is None:
        return jsonify({"error": "question_id và score là bắt buộc"}), 400

    attempt = ExamAttempt.query.get_or_404(attempt_id)
    exam = attempt.exam

    # Kiểm tra quyền: chỉ giáo viên tạo đề mới chấm được
    teacher_id = data.get("teacher_id")
    if exam.created_by != teacher_id:
        return jsonify({"error": "Bạn không có quyền chấm bài này"}), 403

    answer = Answer.query.filter_by(attempt_id=attempt_id, question_id=question_id).first()
    if not answer:
        return jsonify({"error": "Không tìm thấy câu trả lời"}), 404

    old_score = answer.score or 0.0
    answer.score = float(score)

    # Cập nhật tổng điểm
    attempt.total_score = (attempt.total_score or 0.0) - old_score + float(score)
    db.session.commit()

    return jsonify({"message": "Chấm điểm thành công", "total_score": attempt.total_score}), 200


@exam_bp.route("/<int:exam_id>/update-answer", methods=["POST"])
def update_exam_answer(exam_id: int):
    """
    Sửa đáp án đúng và TỰ ĐỘNG CHẤM LẠI ĐIỂM cho tất cả bài làm.
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    question_id = data.get("question_id")
    correct_option_id = data.get("correct_option_id")

    exam = Exam.query.get_or_404(exam_id)
    if exam.created_by != user_id:
        return jsonify({"error": "Bạn không có quyền sửa đề này"}), 403

    question = Question.query.filter_by(id=question_id, exam_id=exam_id).first()
    if not question:
        return jsonify({"error": "Không tìm thấy câu hỏi"}), 404

    if question.question_type != "mcq":
        return jsonify({"error": "Chỉ có thể sửa đáp án trắc nghiệm"}), 400

    try:
        # --- BƯỚC 1: Cập nhật đáp án đúng trong bảng Option ---
        # Reset tất cả options của câu hỏi này về False
        for opt in question.options:
            opt.is_correct = False
        
        # Set option mới thành True
        new_correct_option = Option.query.filter_by(id=correct_option_id, question_id=question_id).first()
        if not new_correct_option:
            return jsonify({"error": "Không tìm thấy đáp án được chọn"}), 404
        
        new_correct_option.is_correct = True
        
        # --- BƯỚC 2: Rà soát và chấm lại điểm (Re-grade) ---
        # Lấy tất cả bài làm của đề thi này
        attempts = ExamAttempt.query.filter_by(exam_id=exam_id).all()
        
        count_updated = 0
        
        for attempt in attempts:
            # Tìm câu trả lời của học sinh cho câu hỏi này
            # (Lọc trong list answers của attempt để tránh query nhiều lần)
            student_answer = next((a for a in attempt.answers if a.question_id == question_id), None)
            
            if student_answer:
                # Kiểm tra lại đáp án
                old_score = student_answer.score
                
                if student_answer.selected_option_id == correct_option_id:
                    # Nếu chọn đúng đáp án mới -> Full điểm
                    student_answer.score = question.score
                else:
                    # Nếu chọn sai -> 0 điểm
                    student_answer.score = 0.0
                
                # Cập nhật tổng điểm của bài làm (trừ điểm cũ, cộng điểm mới)
                attempt.total_score = (attempt.total_score or 0.0) - (old_score or 0.0) + student_answer.score
                count_updated += 1

        db.session.commit()

        return jsonify({
            "message": "Cập nhật đáp án thành công", 
            "re_graded_count": count_updated
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error update answer: {str(e)}")
        return jsonify({"error": "Lỗi server khi cập nhật đáp án", "details": str(e)}), 500


@exam_bp.route("/attempts/<int:attempt_id>", methods=["GET"])
def get_attempt_detail(attempt_id: int):
    """Lấy chi tiết một bài làm (cho học sinh xem lại)."""
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "user_id là bắt buộc"}), 400

    attempt = ExamAttempt.query.get_or_404(attempt_id)
    if attempt.user_id != user_id:
        return jsonify({"error": "Bạn không có quyền xem bài làm này"}), 403

    exam = attempt.exam
    return jsonify(
        {
            "attempt_id": attempt.id,
            "exam_id": exam.id,
            "exam_title": exam.title,
            "total_score": attempt.total_score,
            "start_time": attempt.start_time.isoformat() if attempt.start_time else None,
            "end_time": attempt.end_time.isoformat() if attempt.end_time else None,
            "questions": [
                {
                    "id": q.id,
                    "content": q.content,
                    "question_type": q.question_type,
                    "score": q.score,
                    "options": [
                        {
                            "id": o.id,
                            "content": o.content,
                        }
                        for o in q.options
                    ]
                    if q.question_type == "mcq"
                    else [],
                }
                for q in exam.questions
            ],
            "answers": [
                {
                    "question_id": ans.question_id,
                    "selected_option_id": ans.selected_option_id,
                    "essay_answer": ans.essay_answer,
                    "score": ans.score,
                }
                for ans in attempt.answers
            ],
        }
    )
