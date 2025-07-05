from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from database.config import db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://thinh:1@MEDU\\SQLEXPRESS/PythonProject?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Import sau khi app và db đã init
from auth import auth
from courses import courses
from lessons import lessons
from database.heath import heath, init_db
from database.model import User
from assignments import assignments
from users import users
from notifications import notifications
from admin import admin
from comments import comments
from certificates import certificates
from payments import payments

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(courses)
app.register_blueprint(lessons)
app.register_blueprint(heath)
app.register_blueprint(assignments)
app.register_blueprint(users)
app.register_blueprint(notifications)
app.register_blueprint(admin)
app.register_blueprint(comments)
app.register_blueprint(certificates)
app.register_blueprint(payments)

init_db(app)

@app.route('/')
def index():
    return redirect(url_for('courses.index'))

@app.route('/student/dashboard')
def student_dashboard():
    return render_template('student/dashboard.html')

@app.route('/teacher/dashboard')
def teacher_dashboard():
    return render_template('teacher/dashboard.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/student/assignments')
def student_assignments():
    return render_template('student/assignments.html')

@app.route('/teacher/assignments')
def teacher_assignments():
    return render_template('teacher/assignments.html')

@app.route('/student/code-editor')
def code_editor():
    return render_template('student/code_editor.html')

@app.route('/notifications')
def notifications():
    return render_template('notifications.html')

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/student/rate-course')
def rate_course():
    return render_template('student/rate_course.html')

@app.route('/teacher/upload-material')
def upload_material():
    return render_template('teacher/upload_material.html')

@app.route('/student/feedback')
def student_feedback():
    return render_template('student/feedback.html')

@app.route('/admin/reports')
def admin_reports():
    return render_template('admin/reports.html')

if __name__ == '__main__':
    app.run(debug=True) 