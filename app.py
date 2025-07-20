from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from database.config import db
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import requests
import base64
import json
import time
import os

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
from database.model import User, Assignment, Course, Lesson, Module, AssignmentSubmission, Quiz, QuizQuestion, QuizOption, QuizSubmission, QuizAnswer
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

# Custom Jinja2 filters
@app.template_filter('timeago')
def timeago_filter(date):
    """Convert datetime to 'time ago' format"""
    if not date:
        return "Unknown"
    
    now = datetime.now()
    diff = now - date
    
    if diff.days > 0:
        if diff.days == 1:
            return "1 ngày trước"
        elif diff.days < 7:
            return f"{diff.days} ngày trước"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} tuần trước"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} tháng trước"
        else:
            years = diff.days // 365
            return f"{years} năm trước"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} giờ trước"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} phút trước"
    else:
        return "Vừa xong"

@app.template_filter('from_json')
def from_json_filter(json_string):
    """Parse JSON string to Python object"""
    if not json_string:
        return []
    try:
        return json.loads(json_string)
    except:
        return []

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

@app.route('/code-editor')
def simple_code_editor():
    """Giao diện code editor đơn giản như W3Schools"""
    return render_template('student/simple_code_editor.html')

@app.route('/student/code-editor')
@login_required
def code_editor():
    """Giao diện code editor demo - không cần assignment_id"""
    # Tạo dữ liệu mẫu cho demo
    demo_assignment = {
        'id': 1,
        'title': 'Demo: Tính tổng dãy số',
        'description': 'Viết chương trình tính tổng các số từ 1 đến n',
        'language': 'python',
        'max_score': 100,
        'time_limit': 30,
        'max_submissions': 3,
        'test_cases': json.dumps([
            {"input": "5", "output": "15"},
            {"input": "10", "output": "55"}
        ])
    }
    
    return render_template('student/code_editor.html', 
                         assignment=demo_assignment,
                         existing_submission=None,
                         existing_submissions=[])

@app.route('/notifications')
def notifications():
    # Lấy trang hiện tại từ query parameter
    page = request.args.get('page', 1, type=int)
    
    # Tạo dữ liệu mẫu cho notifications (sẽ thay bằng query database sau)
    sample_notifications = [
        {
            'id': 1,
            'title': 'Bài tập mới được giao',
            'message': 'Giảng viên đã giao bài tập mới cho khóa học Python cơ bản',
            'type': 'assignment',
            'is_read': False,
            'created_at': datetime.now() - timedelta(hours=2),
            'action_url': '/assignments/1'
        },
        {
            'id': 2,
            'title': 'Khóa học mới khai giảng',
            'message': 'Khóa học Perl nâng cao sẽ bắt đầu vào tuần tới',
            'type': 'course',
            'is_read': True,
            'created_at': datetime.now() - timedelta(days=1),
            'action_url': '/courses/2'
        },
        {
            'id': 3,
            'title': 'Điểm bài tập đã được cập nhật',
            'message': 'Bạn đã nhận được 85/100 điểm cho bài tập Python',
            'type': 'grade',
            'is_read': False,
            'created_at': datetime.now() - timedelta(hours=5),
            'action_url': '/submission/3'
        }
    ]
    
    # Phân trang đơn giản
    per_page = 10
    total_notifications = len(sample_notifications)
    total_pages = (total_notifications + per_page - 1) // per_page
    
    # Lấy notifications cho trang hiện tại
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    current_notifications = sample_notifications[start_idx:end_idx]
    
    return render_template('notifications.html',
                         notifications=current_notifications,
                         total_pages=total_pages,
                         current_page=page)

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/student/rate-course')
def rate_course():
    return render_template('student/rate_course.html')

@app.route('/teacher/upload-material', methods=['GET', 'POST'])
def upload_material():
    if request.method == 'POST':
        # Xử lý upload file (sẽ implement sau)
        flash('Chức năng upload đang được phát triển!', 'info')
        return redirect(url_for('upload_material'))
    
    # Lấy danh sách courses cho dropdown (tạm thời lấy tất cả)
    courses = Course.query.all()
    
    # Tạm thời tạo dữ liệu mẫu cho recent_materials
    # Trong thực tế sẽ lấy từ database
    recent_materials = []
    
    return render_template('teacher/upload_material.html', 
                         courses=courses, 
                         recent_materials=recent_materials)

@app.route('/teacher/feedbacks')
def teacher_feedbacks():
    return render_template('teacher/feedbacks.html')

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
    language = request.form.get('language')
    test_cases = request.form.get('test_cases')
    time_limit = request.form.get('time_limit', type=int)
    max_submissions = request.form.get('max_submissions', type=int, default=3)
    due_date = request.form.get('due_date')
    max_score = request.form.get('max_score', type=float)
    course_id = request.form.get('course_id', type=int)
    is_active = request.form.get('is_active') == 'on'
    allow_late_submission = request.form.get('allow_late_submission') == 'on'

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

    # Parse due date
    due_date_obj = None
    if due_date:
        try:
            due_date_obj = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
        except:
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%dT%H:%M')

    assignment = Assignment(
        lesson_id=lesson.id,
        title=title,
        description=description,
        type=type_,
        language=language,
        test_cases=test_cases,
        time_limit=time_limit,
        max_submissions=max_submissions,
        due_date=due_date_obj,
        max_score=max_score or 100.0,
        is_active=is_active,
        allow_late_submission=allow_late_submission,
        created_at=datetime.now()
    )
    db.session.add(assignment)
    db.session.commit()
    flash('Assignment created successfully!', 'success')
    return redirect(url_for('teacher_assignments'))

@app.route('/create-sample-programming-assignment')
@login_required
def create_sample_programming_assignment():
    """Tạo bài tập lập trình mẫu để demo"""
    if current_user.role != 'teacher':
        flash('Permission denied!', 'danger')
        return redirect(url_for('teacher_assignments'))
    
    # Tìm course đầu tiên của teacher
    course = Course.query.filter_by(teacher_id=current_user.id).first()
    if not course:
        flash('You need to create a course first!', 'warning')
        return redirect(url_for('courses.create_course_form'))
    
    # Tìm lesson đầu tiên
    lesson = None
    if course.modules:
        for module in course.modules:
            if module.lessons:
                lesson = module.lessons[0]
                break
    
    if not lesson:
        flash('Course must have at least one lesson!', 'warning')
        return redirect(url_for('lessons.manage_course_content', course_id=course.id))
    
    # Test cases cho bài tập tính tổng
    test_cases = [
        {"input": "5", "output": "15", "description": "Tính tổng từ 1 đến 5"},
        {"input": "10", "output": "55", "description": "Tính tổng từ 1 đến 10"},
        {"input": "1", "output": "1", "description": "Tính tổng từ 1 đến 1"}
    ]
    
    assignment = Assignment(
        lesson_id=lesson.id,
        title="Bài tập 1: Tính tổng dãy số",
        description="""
**Mô tả bài tập:**
Viết chương trình tính tổng các số từ 1 đến n, trong đó n là số nguyên dương được nhập từ bàn phím.

**Yêu cầu:**
- Input: Một số nguyên n (1 ≤ n ≤ 1000)
- Output: Tổng các số từ 1 đến n

**Ví dụ:**
- Input: 5
- Output: 15 (vì 1+2+3+4+5 = 15)

**Lưu ý:**
- Chương trình phải xử lý được các trường hợp đặc biệt
- Code phải rõ ràng, có comment giải thích
- Tuân thủ quy tắc đặt tên biến
        """,
        type='code',
        language='python',
        test_cases=json.dumps(test_cases),
        time_limit=30,
        max_submissions=3,
        due_date=datetime.now() + timedelta(days=7),
        max_score=100.0,
        is_active=True,
        allow_late_submission=True,
        created_at=datetime.now()
    )
    
    db.session.add(assignment)
    db.session.commit()
    
    flash('Sample programming assignment created successfully!', 'success')
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

#chatbox
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3:mini"
@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    payload_generate = {
        "model": OLLAMA_MODEL,
        "prompt": user_message,
        "stream": False,
         "options": {
            "num_predict": 1024  # hoặc 128 nếu vẫn chậm
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload_generate, timeout=60)
        data = response.json()
        content = data.get('response') or '[Không có phản hồi từ AI]'
        return jsonify({'response': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/teacher/quiz/create', methods=['GET', 'POST'])
@login_required
def teacher_create_quiz():
    """Tạo bài trắc nghiệm mới"""
    if current_user.role != 'teacher':
        flash('Permission denied!', 'danger')
        return redirect(url_for('teacher_assignments'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        time_limit = request.form.get('time_limit', type=int)
        max_attempts = request.form.get('max_attempts', type=int, default=1)
        shuffle_questions = request.form.get('shuffle_questions') == 'on'
        show_correct_answers = request.form.get('show_correct_answers') == 'on'
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
            flash('Course must have at least one lesson!', 'danger')
            return redirect(url_for('teacher_create_quiz'))
        
        # Tạo assignment cho quiz
        assignment = Assignment(
            lesson_id=lesson.id,
            title=title,
            description=description,
            type='quiz',
            max_score=100.0,
            is_active=True,
            created_at=datetime.now()
        )
        db.session.add(assignment)
        db.session.flush()  # Để lấy assignment.id
        
        # Tạo quiz
        quiz = Quiz(
            assignment_id=assignment.id,
            title=title,
            description=description,
            time_limit=time_limit,
            max_attempts=max_attempts,
            shuffle_questions=shuffle_questions,
            show_correct_answers=show_correct_answers,
            created_at=datetime.now()
        )
        db.session.add(quiz)
        db.session.commit()
        
        flash('Quiz created successfully! Now add questions.', 'success')
        return redirect(url_for('teacher_edit_quiz', quiz_id=quiz.id))
    
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher/quiz_create.html', courses=courses)

@app.route('/teacher/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def teacher_edit_quiz(quiz_id):
    """Chỉnh sửa bài trắc nghiệm và thêm câu hỏi"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Kiểm tra quyền
    if current_user.role != 'teacher' or quiz.assignment.lesson.module.course.teacher_id != current_user.id:
        flash('Permission denied!', 'danger')
        return redirect(url_for('teacher_assignments'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_question':
            question_text = request.form.get('question_text')
            question_type = request.form.get('question_type', 'multiple_choice')
            points = request.form.get('points', type=float, default=1.0)
            
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=question_text,
                question_type=question_type,
                points=points,
                order_index=len(quiz.questions) + 1,
                created_at=datetime.now()
            )
            db.session.add(question)
            db.session.flush()
            
            # Thêm các lựa chọn
            if question_type == 'multiple_choice':
                for i in range(1, 5):  # 4 lựa chọn
                    option_text = request.form.get(f'option_{i}')
                    is_correct = request.form.get(f'correct_option') == str(i)
                    
                    if option_text:
                        option = QuizOption(
                            question_id=question.id,
                            option_text=option_text,
                            is_correct=is_correct,
                            order_index=i,
                            created_at=datetime.now()
                        )
                        db.session.add(option)
            
            db.session.commit()
            flash('Question added successfully!', 'success')
            
        elif action == 'update_quiz':
            quiz.title = request.form.get('title')
            quiz.description = request.form.get('description')
            quiz.time_limit = request.form.get('time_limit', type=int)
            quiz.max_attempts = request.form.get('max_attempts', type=int, default=1)
            quiz.shuffle_questions = request.form.get('shuffle_questions') == 'on'
            quiz.show_correct_answers = request.form.get('show_correct_answers') == 'on'
            
            db.session.commit()
            flash('Quiz updated successfully!', 'success')
            
        elif action == 'delete_question':
            question_id = request.form.get('question_id', type=int)
            question = QuizQuestion.query.get(question_id)
            if question and question.quiz_id == quiz.id:
                db.session.delete(question)
                db.session.commit()
                flash('Question deleted successfully!', 'success')
    
    return render_template('teacher/quiz_edit.html', quiz=quiz)

@app.route('/student/quiz/<int:quiz_id>/take', methods=['GET', 'POST'])
@login_required
def student_take_quiz(quiz_id):
    """Học sinh làm bài trắc nghiệm"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Kiểm tra xem đã làm bài chưa
    existing_submission = QuizSubmission.query.filter_by(
        quiz_id=quiz.id,
        user_id=current_user.id
    ).first()
    
    if existing_submission and existing_submission.submitted_at:
        flash('You have already taken this quiz!', 'warning')
        return redirect(url_for('student_view_quiz_result', submission_id=existing_submission.id))
    
    if request.method == 'POST':
        # Xử lý nộp bài
        start_time = request.form.get('start_time', type=int)
        time_taken = int(time.time()) - start_time if start_time else 0
        
        submission = QuizSubmission(
            quiz_id=quiz.id,
            user_id=current_user.id,
            time_taken=time_taken,
            submitted_at=datetime.now()
        )
        db.session.add(submission)
        db.session.flush()
        
        total_score = 0
        max_score = 0
        
        # Xử lý từng câu trả lời
        for question in quiz.questions:
            max_score += question.points
            
            if question.question_type == 'multiple_choice':
                selected_option_id = request.form.get(f'question_{question.id}', type=int)
                if selected_option_id:
                    selected_option = QuizOption.query.get(selected_option_id)
                    is_correct = selected_option and selected_option.is_correct
                    points_earned = question.points if is_correct else 0
                    total_score += points_earned
                    
                    answer = QuizAnswer(
                        submission_id=submission.id,
                        question_id=question.id,
                        selected_option_id=selected_option_id,
                        is_correct=is_correct,
                        points_earned=points_earned,
                        created_at=datetime.now()
                    )
                    db.session.add(answer)
            
            elif question.question_type == 'text':
                answer_text = request.form.get(f'question_{question.id}')
                # Đơn giản hóa: so sánh chuỗi (trong thực tế có thể dùng AI)
                correct_option = QuizOption.query.filter_by(
                    question_id=question.id,
                    is_correct=True
                ).first()
                
                is_correct = correct_option and answer_text.lower().strip() == correct_option.option_text.lower().strip()
                points_earned = question.points if is_correct else 0
                total_score += points_earned
                
                answer = QuizAnswer(
                    submission_id=submission.id,
                    question_id=question.id,
                    answer_text=answer_text,
                    is_correct=is_correct,
                    points_earned=points_earned,
                    created_at=datetime.now()
                )
                db.session.add(answer)
        
        submission.score = total_score
        submission.max_score = max_score
        db.session.commit()
        
        flash('Quiz submitted successfully!', 'success')
        return redirect(url_for('student_view_quiz_result', submission_id=submission.id))
    
    # Hiển thị form làm bài
    return render_template('student/quiz_take.html', quiz=quiz)

@app.route('/student/quiz/result/<int:submission_id>')
@login_required
def student_view_quiz_result(submission_id):
    """Xem kết quả bài trắc nghiệm"""
    submission = QuizSubmission.query.get_or_404(submission_id)
    
    # Kiểm tra quyền xem
    if submission.user_id != current_user.id and current_user.role not in ['teacher', 'admin']:
        flash('Permission denied!', 'danger')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student/quiz_result.html', submission=submission)

@app.route('/student/code-editor/<int:assignment_id>')
@login_required
def student_code_editor(assignment_id):
    """Giao diện code editor cho sinh viên làm bài lập trình"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Kiểm tra xem đã nộp bài chưa
    existing_submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id,
        user_id=current_user.id
    ).order_by(AssignmentSubmission.submitted_at.desc()).first()
    
    # Lấy tất cả bài nộp của sinh viên
    existing_submissions = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id,
        user_id=current_user.id
    ).all()
    
    return render_template('student/code_editor.html', 
                         assignment=assignment,
                         existing_submission=existing_submission,
                         existing_submissions=existing_submissions)

@app.route('/assignments/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    """Xử lý nộp bài lập trình"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Kiểm tra thời gian nộp
    if assignment.due_date and datetime.now() > assignment.due_date:
        if not assignment.allow_late_submission:
            flash('Đã hết hạn nộp bài!', 'danger')
            return redirect(url_for('student_code_editor', assignment_id=assignment_id))
    
    # Kiểm tra số lần nộp
    existing_submissions = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id,
        user_id=current_user.id
    ).count()
    
    if existing_submissions >= assignment.max_submissions:
        flash(f'Bạn đã nộp bài {assignment.max_submissions} lần!', 'warning')
        return redirect(url_for('student_code_editor', assignment_id=assignment_id))
    
    # Xử lý nộp bài
    content = request.form.get('code')
    start_time = request.form.get('start_time', type=int)
    time_taken = int(time.time()) - start_time if start_time else 0
    
    submission = AssignmentSubmission(
        assignment_id=assignment_id,
        user_id=current_user.id,
        content=content,
        submitted_at=datetime.now(),
        time_taken=time_taken
    )
    
    # Chấm điểm tự động cho bài tập lập trình
    if assignment.type == 'code' and assignment.test_cases:
        test_results = auto_grade_code(content, assignment.test_cases, assignment.language)
        submission.test_results = json.dumps(test_results)
        submission.score = sum(result['score'] for result in test_results)
    
    db.session.add(submission)
    db.session.commit()
    
    flash('Nộp bài thành công!', 'success')
    return redirect(url_for('view_submission_result', submission_id=submission.id))

@app.route('/submission/result/<int:submission_id>')
@login_required
def view_submission_result(submission_id):
    """Xem kết quả bài nộp"""
    submission = AssignmentSubmission.query.get_or_404(submission_id)
    
    # Kiểm tra quyền xem
    if submission.user_id != current_user.id and current_user.role not in ['teacher', 'admin']:
        flash('Permission denied!', 'danger')
        return redirect(url_for('student_dashboard'))
    
    assignment = submission.assignment
    existing_submissions = AssignmentSubmission.query.filter_by(
        assignment_id=assignment.id,
        user_id=current_user.id
    ).all()
    
    return render_template('student/submission_result.html', 
                         submission=submission,
                         assignment=assignment,
                         existing_submissions=existing_submissions)

def auto_grade_code(code, test_cases, language):
    """Hệ thống chấm điểm tự động"""
    test_cases = json.loads(test_cases) if isinstance(test_cases, str) else test_cases
    results = []
    
    for i, test_case in enumerate(test_cases):
        try:
            input_val = test_case['input']
            expected = test_case['output']
            
            # Mô phỏng chạy code với input
            # Trong thực tế sẽ gọi API Judge0
            if language == 'python':
                # Đơn giản hóa: mô phỏng kết quả
                if "range(1, n + 1)" in code and "total += i" in code:
                    actual = str(sum(range(1, int(input_val) + 1)))
                    passed = actual == expected
                elif "n * (n + 1) // 2" in code:
                    n = int(input_val)
                    actual = str(n * (n + 1) // 2)
                    passed = actual == expected
                else:
                    actual = "Error"
                    passed = False
            else:
                actual = "Language not supported"
                passed = False
            
            score = 25 if passed else 0  # 25 điểm cho mỗi test case
            results.append({
                "test_case": i + 1,
                "input": input_val,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "score": score
            })
            
        except Exception as e:
            results.append({
                "test_case": i + 1,
                "input": input_val,
                "expected": expected,
                "actual": f"Error: {str(e)}",
                "passed": False,
                "score": 0
            })
    
    return results

@app.route('/student/file-upload/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def student_file_upload(assignment_id):
    """Giao diện upload file bài tập"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Kiểm tra thời gian nộp
    if assignment.due_date and datetime.now() > assignment.due_date:
        if not assignment.allow_late_submission:
            flash('Đã hết hạn nộp bài!', 'danger')
            return redirect(url_for('assignments.view_assignment', assignment_id=assignment_id))
    
    # Lấy tất cả bài nộp của sinh viên
    existing_submissions = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id,
        user_id=current_user.id
    ).all()
    
    if request.method == 'POST':
        # Xử lý upload file
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Không có file được chọn'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Không có file được chọn'})
        
        # Kiểm tra loại file
        allowed_extensions = {
            'code': ['.py', '.pl', '.txt', '.zip'],
            'document': ['.pdf', '.doc', '.docx', '.txt']
        }
        
        file_ext = '.' + file.filename.rsplit('.', 1)[1].lower()
        assignment_type = 'code' if assignment.type == 'code' else 'document'
        
        if file_ext not in allowed_extensions[assignment_type]:
            return jsonify({'success': False, 'message': f'Loại file không được hỗ trợ. Hỗ trợ: {", ".join(allowed_extensions[assignment_type])}'})
        
        # Kiểm tra kích thước file (10MB)
        if len(file.read()) > 10 * 1024 * 1024:
            return jsonify({'success': False, 'message': 'File quá lớn. Kích thước tối đa là 10MB'})
        
        file.seek(0)  # Reset file pointer
        
        # Kiểm tra số lần nộp
        if len(existing_submissions) >= assignment.max_submissions:
            return jsonify({'success': False, 'message': f'Bạn đã nộp bài {assignment.max_submissions} lần!'})
        
        # Tạo thư mục lưu file
        upload_dir = os.path.join('static', 'uploads', 'submissions', str(assignment_id), str(current_user.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Lưu file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Đọc nội dung file nếu là text
        content = ""
        if file_ext in ['.py', '.pl', '.txt']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                content = "Không thể đọc nội dung file"
        
        # Tạo submission
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            user_id=current_user.id,
            filename=filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            file_type=file.content_type,
            content=content,
            notes=request.form.get('notes', ''),
            submitted_at=datetime.now()
        )
        
        db.session.add(submission)
        db.session.commit()
        
        flash('Nộp bài thành công!', 'success')
        return jsonify({
            'success': True, 
            'message': 'Nộp bài thành công!',
            'redirect_url': url_for('view_submission_detail', submission_id=submission.id)
        })
    
    return render_template('student/file_upload.html', 
                         assignment=assignment,
                         existing_submissions=existing_submissions)

@app.route('/submission/<int:submission_id>/detail')
@login_required
def view_submission_detail(submission_id):
    """Xem chi tiết bài nộp file"""
    submission = AssignmentSubmission.query.get_or_404(submission_id)
    
    # Kiểm tra quyền xem
    if submission.user_id != current_user.id and current_user.role not in ['teacher', 'admin']:
        flash('Permission denied!', 'danger')
        return redirect(url_for('student_dashboard'))
    
    assignment = submission.assignment
    existing_submissions = AssignmentSubmission.query.filter_by(
        assignment_id=assignment.id,
        user_id=current_user.id
    ).all()
    
    return render_template('student/file_submission_detail.html', 
                         submission=submission,
                         assignment=assignment,
                         existing_submissions=existing_submissions)

@app.route('/submission/<int:submission_id>/download')
@login_required
def download_submission_file(submission_id):
    """Download file bài nộp"""
    submission = AssignmentSubmission.query.get_or_404(submission_id)
    
    # Kiểm tra quyền download
    if submission.user_id != current_user.id and current_user.role not in ['teacher', 'admin']:
        flash('Permission denied!', 'danger')
        return redirect(url_for('student_dashboard'))
    
    if not os.path.exists(submission.file_path):
        flash('File không tồn tại!', 'danger')
        return redirect(url_for('view_submission_detail', submission_id=submission_id))
    
    return send_file(submission.file_path, as_attachment=True, download_name=submission.filename)

@app.route('/create-sample-quiz')
@login_required
def create_sample_quiz():
    """Tạo bài trắc nghiệm mẫu để demo"""
    if current_user.role != 'teacher':
        flash('Permission denied!', 'danger')
        return redirect(url_for('teacher_assignments'))
    
    # Tìm course đầu tiên của teacher
    course = Course.query.filter_by(teacher_id=current_user.id).first()
    if not course:
        flash('You need to create a course first!', 'warning')
        return redirect(url_for('courses.create_course_form'))
    
    # Tìm lesson đầu tiên
    lesson = None
    if course.modules:
        for module in course.modules:
            if module.lessons:
                lesson = module.lessons[0]
                break
    
    if not lesson:
        flash('Course must have at least one lesson!', 'warning')
        return redirect(url_for('lessons.manage_course_content', course_id=course.id))
    
    # Tạo assignment cho quiz
    assignment = Assignment(
        lesson_id=lesson.id,
        title="Bài trắc nghiệm: Kiến thức Python cơ bản",
        description="""
**Mô tả bài trắc nghiệm:**
Bài trắc nghiệm này kiểm tra kiến thức cơ bản về Python, bao gồm:
- Cú pháp cơ bản
- Cấu trúc dữ liệu
- Vòng lặp và điều kiện
- Hàm và module

**Thời gian làm bài:** 15 phút
**Số câu hỏi:** 10 câu
**Điểm tối đa:** 100 điểm
        """,
        type='quiz',
        max_score=100.0,
        is_active=True,
        created_at=datetime.now()
    )
    db.session.add(assignment)
    db.session.flush()
    
    # Tạo quiz
    quiz = Quiz(
        assignment_id=assignment.id,
        title="Bài trắc nghiệm: Kiến thức Python cơ bản",
        description="Kiểm tra kiến thức cơ bản về Python",
        time_limit=15,
        max_attempts=1,
        shuffle_questions=True,
        show_correct_answers=True,
        created_at=datetime.now()
    )
    db.session.add(quiz)
    db.session.flush()
    
    # Tạo các câu hỏi mẫu
    sample_questions = [
        {
            "text": "Trong Python, cách nào sau đây để khai báo một biến?",
            "options": [
                {"text": "var x = 5", "correct": False},
                {"text": "let x = 5", "correct": False},
                {"text": "x = 5", "correct": True},
                {"text": "const x = 5", "correct": False}
            ],
            "points": 10
        },
        {
            "text": "Hàm nào dùng để in ra màn hình trong Python?",
            "options": [
                {"text": "console.log()", "correct": False},
                {"text": "print()", "correct": True},
                {"text": "echo()", "correct": False},
                {"text": "printf()", "correct": False}
            ],
            "points": 10
        },
        {
            "text": "Cấu trúc dữ liệu nào sau đây có thể thay đổi trong Python?",
            "options": [
                {"text": "Tuple", "correct": False},
                {"text": "String", "correct": False},
                {"text": "List", "correct": True},
                {"text": "Frozen Set", "correct": False}
            ],
            "points": 10
        },
        {
            "text": "Vòng lặp for trong Python có thể lặp qua:",
            "options": [
                {"text": "Chỉ số nguyên", "correct": False},
                {"text": "Chỉ chuỗi", "correct": False},
                {"text": "Chỉ list", "correct": False},
                {"text": "Tất cả các đối tượng có thể lặp (iterable)", "correct": True}
            ],
            "points": 10
        },
        {
            "text": "Cách nào để tạo một list rỗng trong Python?",
            "options": [
                {"text": "list = []", "correct": True},
                {"text": "list = {}", "correct": False},
                {"text": "list = ()", "correct": False},
                {"text": "list = None", "correct": False}
            ],
            "points": 10
        }
    ]
    
    for i, q_data in enumerate(sample_questions, 1):
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q_data["text"],
            question_type='multiple_choice',
            points=q_data["points"],
            order_index=i,
            created_at=datetime.now()
        )
        db.session.add(question)
        db.session.flush()
        
        for j, opt_data in enumerate(q_data["options"], 1):
            option = QuizOption(
                question_id=question.id,
                option_text=opt_data["text"],
                is_correct=opt_data["correct"],
                order_index=j,
                created_at=datetime.now()
            )
            db.session.add(option)
    
    db.session.commit()
    flash('Sample quiz created successfully!', 'success')
    return redirect(url_for('teacher_edit_quiz', quiz_id=quiz.id))

@app.route('/simple-upload')
def simple_upload():
    """Giao diện upload file đơn giản"""
    return render_template('student/simple_upload.html')

@app.route('/create-sample-assignment')
@login_required
def create_sample_assignment():
    """Tạo bài tập mẫu để test"""
    # Tạo lesson mẫu nếu chưa có
    lesson = Lesson.query.filter_by(id=1).first()
    if not lesson:
        lesson = Lesson(
            id=1,
            title="Bài học mẫu",
            description="Bài học mẫu để test",
            module_id=1,
            order_index=1,
            lesson_type="assignment",
            duration_minutes=60,
            is_active=True
        )
        db.session.add(lesson)
        db.session.commit()
    
    # Tạo assignment cho file upload
    assignment = Assignment(
        lesson_id=lesson.id,
        title="Bài tập mẫu - Upload file Python",
        description="Viết chương trình Python tính tổng từ 1 đến n và upload file code",
        type="code",
        language="python",
        max_score=100.0,
        time_limit=60,
        max_submissions=5,
        due_date=datetime.now() + timedelta(days=7),
        allow_late_submission=True,
        test_cases=json.dumps([
            {"input": "5", "output": "15", "description": "Tính tổng từ 1 đến 5"},
            {"input": "10", "output": "55", "description": "Tính tổng từ 1 đến 10"},
            {"input": "1", "output": "1", "description": "Tính tổng từ 1 đến 1"}
        ])
    )
    db.session.add(assignment)
    db.session.commit()
    
    flash('Đã tạo bài tập mẫu thành công! ID: ' + str(assignment.id), 'success')
    return redirect(url_for('assignments.view_assignment', assignment_id=assignment.id))

if __name__ == '__main__':
    app.run(debug=True) 