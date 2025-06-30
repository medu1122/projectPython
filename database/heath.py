from flask import current_app, Blueprint, jsonify
from database.config import db
from sqlalchemy import text

# Tạo blueprint cho heath check
heath = Blueprint('heath', __name__)

# Biến để theo dõi đã khởi tạo hay chưa
_is_initialized = False

@heath.route('/heath', methods=['GET'])
def heath_check():
    """Endpoint kiểm tra sức khỏe hệ thống"""
    is_connected = check_db_connection()
    
    response = {
        "status": "healthy" if is_connected else "unhealthy",
        "database": {
            "connected": is_connected
        },
        "application": {
            "running": True
        }
    }
    
    status_code = 200 if is_connected else 503
    return jsonify(response), status_code

@heath.route('/heath/db', methods=['GET'])
def db_info():
    """Endpoint hiển thị thông tin cơ sở dữ liệu"""
    is_connected = check_db_connection()
    
    response = {
        "connection": {
            "status": is_connected
        },
        "config": {
            "db_uri": mask_db_password(current_app.config['SQLALCHEMY_DATABASE_URI'])
        }
    }
    
    return jsonify(response)

def init_db(app):
    """
    Hàm khởi tạo cơ sở dữ liệu - gồm kiểm tra kết nối và tạo bảng.
    """
    global _is_initialized
    
    # Nếu đã khởi tạo rồi thì không làm lại
    if _is_initialized:
        return True
    
    with app.app_context():
        # Kiểm tra kết nối
        if check_db_connection():
            print("DB Connected: TRUE")
            try:
                # Cố gắng tạo bảng, bỏ qua nếu đã tồn tại
                db.create_all()
                print("DB Tables: CREATED/VERIFIED")
            except Exception as e:
                # Nếu bảng đã tồn tại, chỉ in warning
                if "already an object named" in str(e):
                    print("DB Tables: ALREADY EXIST - SKIPPING")
                else:
                    print(f"DB Tables: ERROR - {e}")
                    # Vẫn có thể tiếp tục nếu bảng đã tồn tại
            _is_initialized = True
            return True
        else:
            print("DB Connected: FALSE")
            return False

def check_db_connection():
    """
    Kiểm tra kết nối cơ sở dữ liệu đơn giản.
    
    Returns:
        bool: True nếu kết nối thành công, False nếu thất bại
    """
    try:
        # Sử dụng text() để bọc truy vấn SQL
        db.session.execute(text("SELECT 1")).fetchone()
        return True
    except Exception:
        return False

def mask_db_password(db_uri):
    """
    Ẩn mật khẩu trong chuỗi kết nối cơ sở dữ liệu.
    """
    import re
    # Tìm và thay thế mật khẩu trong URI
    return re.sub(r'://([^:]+):([^@]+)@', r'://\1:******@', db_uri)
