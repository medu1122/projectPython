from flask import Flask, render_template
from flask_login import LoginManager, current_user
from database.config import db, app
from auth import auth
from courses import courses
from lessons import lessons
from database.heath import heath, init_db
from database.model import User

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Make current_user available in all templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(courses)
app.register_blueprint(lessons)
app.register_blueprint(heath)

# Khởi tạo cơ sở dữ liệu
init_db(app)

# Remove duplicate routes now handled by auth blueprint
@app.route('/')
def index():
    return render_template('layout.html')

@app.route('/student/dashboard')
def student_dashboard():
    return render_template('student/dashboard.html')

@app.route('/teacher/dashboard')
def teacher_dashboard():
    return render_template('teacher/dashboard.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

if __name__ == '__main__':
    app.run(debug=True) 