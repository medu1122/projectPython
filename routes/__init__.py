from routes.main import main_bp
from routes.auth import auth_bp
from routes.student import student_bp
from routes.teacher import teacher_bp
from routes.admin import admin_bp
from routes.api import api_bp

# Export all blueprints
__all__ = ['main_bp', 'auth_bp', 'student_bp', 'teacher_bp', 'admin_bp', 'api_bp'] 