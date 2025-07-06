from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from database.config import db
from datetime import datetime
import requests
import base64

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
from database.model import User, Assignment, Course, Lesson
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

@app.route('/teacher/assignments/create', methods=['GET'])
@login_required
def teacher_create_assignment_form():
    if not hasattr(current_user, 'role') or current_user.role != 'teacher':
        flash('Permission denied!', 'danger')
        return redirect(url_for('teacher_assignments'))
    # Lấy danh sách courses mà giáo viên này dạy
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher/assignment_create.html', courses=courses)

@app.route('/teacher/assignments/create', methods=['POST'])
@login_required
def teacher_create_assignment():
    if not hasattr(current_user, 'role') or current_user.role != 'teacher':
        flash('Permission denied!', 'danger')
        return redirect(url_for('teacher_assignments'))

    title = request.form.get('title')
    description = request.form.get('description')
    type_ = request.form.get('type')
    due_date = request.form.get('due_date')
    max_score = request.form.get('max_score', type=float)
    course_id = request.form.get('course_id', type=int)

    # Lấy lesson đầu tiên của course
    course = Course.query.get(course_id)
    lesson = None
    if course and course.modules:
        for module in course.modules:
            if module.lessons:
                lesson = module.lessons[0]
                break
    if not lesson:
        flash('Course must have at least one lesson to create assignment!', 'danger')
        return redirect(url_for('teacher_assignments'))

    assignment = Assignment(
        lesson_id=lesson.id,
        title=title,
        description=description,
        type=type_,
        due_date=due_date,
        max_score=max_score or 100.0,
        created_at=datetime.now()
    )
    db.session.add(assignment)
    db.session.commit()
    flash('Assignment created successfully!', 'success')
    return redirect(url_for('teacher_assignments'))

@app.route('/api/run-code', methods=['POST'])
def api_run_code():
    data = request.get_json()
    code = data.get('code')
    language = data.get('language')
    if not code or not language:
        return jsonify({'success': False, 'error': 'Thiếu code hoặc ngôn ngữ'}), 400

    lang_map = {
        'python': 71,  # Python 3.x
        'perl': 85     # Perl 5
    }
    language_id = lang_map.get(language.lower())
    if not language_id:
        return jsonify({'success': False, 'error': 'Ngôn ngữ không hỗ trợ'}), 400

    def b64encode(s):
        return base64.b64encode(s.encode('utf-8')).decode('utf-8') if s else ''
    def b64decode(s):
        return base64.b64decode(s).decode('utf-8') if s else ''

    try:
        resp = requests.post(
            'https://judge0-ce.p.rapidapi.com/submissions?base64_encoded=true&wait=true',
            headers={
                'Content-Type': 'application/json',
                'X-RapidAPI-Key': 'a90d1bc759msh073241cd26ac790p1f3f29jsn130f109ff3d0',
                'X-RapidAPI-Host': 'judge0-ce.p.rapidapi.com'
            },
            json={
                'source_code': b64encode(code),
                'language_id': language_id
            },
            timeout=15
        )
        def parse_judge0_result(result):
            if result.get('stdout'):
                return {'success': True, 'output': b64decode(result['stdout'])}
            elif result.get('stderr'):
                return {'success': False, 'error': b64decode(result['stderr'])}
            elif result.get('compile_output'):
                return {'success': False, 'error': b64decode(result['compile_output'])}
            else:
                return {'success': False, 'error': 'Không có output từ Judge0'}
        if resp.status_code == 201:
            result = resp.json()
            return jsonify(parse_judge0_result(result))
        elif resp.status_code == 202:
            result = resp.json()
            token = result.get('token')
            if not token:
                return jsonify({'success': False, 'error': 'Không nhận được token từ Judge0'}), 500
            get_resp = requests.get(
                f'https://judge0-ce.p.rapidapi.com/submissions/{token}?base64_encoded=true',
                headers={
                    'X-RapidAPI-Key': 'a90d1bc759msh073241cd26ac790p1f3f29jsn130f109ff3d0',
                    'X-RapidAPI-Host': 'judge0-ce.p.rapidapi.com'
                },
                timeout=15
            )
            if get_resp.status_code == 200:
                get_result = get_resp.json()
                return jsonify(parse_judge0_result(get_result))
            else:
                return jsonify({'success': False, 'error': f'GET Judge0 lỗi: {get_resp.status_code} {get_resp.text}'}), 500
        elif resp.status_code == 200:
            result = resp.json()
            return jsonify(parse_judge0_result(result))
        else:
            return jsonify({'success': False, 'error': f'Judge0 trả về status {resp.status_code}: {resp.text}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 