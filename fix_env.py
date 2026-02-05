import urllib.parse
import os

# --- CẤU HÌNH (Thay mật khẩu thật của bạn vào đây) ---
RAW_PASSWORD = "webkiemtra123" 
# Lưu ý: Giữ nguyên các thông tin khác, chỉ thay password
DB_USER = "postgres.mhwdqwucvgzicrntnqku"
DB_HOST = "aws-1-ap-south-1.pooler.supabase.com"
DB_PORT = "5432"
DB_NAME = "postgres"

def create_clean_env_file():
    # 1. Mã hóa mật khẩu (xử lý các ký tự đặc biệt như @, :, /)
    encoded_password = urllib.parse.quote_plus(RAW_PASSWORD)

    # 2. Tạo chuỗi kết nối chuẩn SQLAlchemy
    # Cú pháp: postgresql://USER:PASSWORD@HOST:PORT/DBNAME
    db_url = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # 3. Nội dung file .env chuẩn (không khoảng trắng thừa)
    env_content = f'DATABASE_URL="{db_url}"'

    # 4. Ghi đè vào file .env
    file_path = os.path.join(os.getcwd(), '.env')
    with open(file_path, 'w') as f:
        f.write(env_content)
    
    print("✅ Đã tạo lại file .env thành công!")
    print(f"📂 File nằm tại: {file_path}")
    print(f"🔗 Nội dung chuỗi kết nối: {db_url}")
    print("\n👉 Bây giờ bạn hãy chạy lại lệnh: flask db upgrade")

if __name__ == "__main__":
    create_clean_env_file()