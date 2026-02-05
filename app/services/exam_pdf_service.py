import pdfplumber
import re
from typing import List, Dict, Any, Optional

class ExamPdfParser:
    def parse_file(self, file_stream) -> List[Dict[str, Any]]:
        questions = []
        
        # Regex nhận diện bắt đầu câu hỏi: 
        # VD: "Câu 1:", "1.", "Bài 1:", "Question 1"
        # Giải thích: ^(từ khóa) + (số) + (dấu chấm/hai chấm/ngoặc) HOẶC (số) + (dấu chấm/hai chấm)
        question_pattern = re.compile(r'^(Câu|Question|Bài)\s*\d+[:\.\)]|^\d+[\.\:\)]')

        # Regex nhận diện bắt đầu đáp án:
        # VD: "A.", "a)", "A/","1." (nếu dùng số thay chữ)
        option_pattern = re.compile(r'^([A-D]|[a-d]|[1-4])[\.\)\/\-]')

        # Các từ khóa để nhận biết dòng chứa đáp án đúng (để bỏ qua)
        answer_keys_pattern = re.compile(r'(đáp án|lời giải|hướng dẫn|answer key|key:)', re.IGNORECASE)

        # Biến trạng thái
        current_question = None
        current_option = None 

        try:
            # pdfplumber có thể đọc trực tiếp từ stream
            with pdfplumber.open(file_stream) as pdf:
                full_text_lines = []
                
                # 1. Trích xuất toàn bộ text theo từng dòng visual
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        # Tách dòng và làm sạch khoảng trắng thừa
                        lines = extracted.split('\n')
                        full_text_lines.extend([line.strip() for line in lines if line.strip()])

                # 2. Quét từng dòng (Scan Line Algorithm)
                for line in full_text_lines:
                    
                    # Nếu gặp dòng chứa "Đáp án đúng: A" thì bỏ qua
                    if answer_keys_pattern.search(line) and len(line) < 50:
                        continue

                    # --- CASE 1: BẮT ĐẦU CÂU HỎI MỚI ---
                    if question_pattern.match(line):
                        # Lưu câu hỏi cũ trước khi tạo câu mới
                        if current_question:
                            questions.append(current_question)
                        
                        # Làm sạch chữ "Câu 1:" để lấy nội dung
                        clean_content = re.sub(question_pattern, '', line).strip()
                        
                        current_question = {
                            "content": clean_content,
                            "question_type": "mcq",
                            "score": 1,
                            "options": []
                        }
                        current_option = None # Reset option

                    # --- CASE 2: BẮT ĐẦU ĐÁP ÁN (A, B, C, D) ---
                    # Chỉ xét nếu đang nằm trong 1 câu hỏi
                    elif current_question and option_pattern.match(line):
                        match = option_pattern.match(line)
                        label = match.group(1).upper() # Lấy chữ cái A, B...
                        
                        # Chuyển số 1-4 thành A-D nếu cần
                        if label in ['1', '2', '3', '4']:
                            mapping = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
                            label = mapping[label]

                        # Lấy nội dung đáp án (bỏ chữ "A." ở đầu)
                        clean_opt_content = re.sub(option_pattern, '', line).strip()

                        new_option = {
                            "content": clean_opt_content,
                            "is_correct": False 
                        }
                        
                        current_question["options"].append(new_option)
                        current_option = new_option # Đánh dấu đang xử lý option này

                    # --- CASE 3: NỘI DUNG NỐI TIẾP (DÒNG DÀI) ---
                    else:
                        if current_question:
                            if current_option:
                                # Nếu đang đứng ở đáp án -> Nối text vào đáp án
                                current_option["content"] += " " + line
                            else:
                                # Nếu chưa có đáp án -> Nối text vào câu hỏi
                                current_question["content"] += " " + line

                # Lưu câu hỏi cuối cùng
                if current_question:
                    questions.append(current_question)

        except Exception as e:
            print(f"Lỗi khi đọc PDF: {e}")
            return []

        return questions