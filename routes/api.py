from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app import db
from models import Course, Module, Lesson, Assignment, Submission, User, ChatSession, ChatMessage
from functools import wraps

api_bp = Blueprint('api', __name__)

# Custom decorator for API authentication
def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Helper function to convert model to dict
def to_dict(model, exclude=None):
    """Convert SQLAlchemy model to dictionary"""
    exclude = exclude or []
    result = {}
    for column in model.__table__.columns:
        if column.name not in exclude:
            result[column.name] = getattr(model, column.name)
    return result

@api_bp.route('/courses', methods=['GET'])
@api_login_required
def get_courses():
    """Get all courses API endpoint"""
    courses = []
    
    if request.args.get('enrolled') == 'true' and current_user.role.name == 'STUDENT':
        # Get enrolled courses for student
        for course in current_user.courses_enrolled:
            courses.append(to_dict(course, exclude=['created_at', 'updated_at']))
    elif request.args.get('teaching') == 'true' and current_user.role.name == 'TEACHER':
        # Get courses taught by teacher
        query = Course.query.filter_by(teacher_id=current_user.id)
        for course in query.all():
            courses.append(to_dict(course, exclude=['created_at', 'updated_at']))
    else:
        # Get all active courses
        query = Course.query.filter_by(is_active=True)
        for course in query.all():
            courses.append(to_dict(course, exclude=['created_at', 'updated_at']))
    
    return jsonify({'courses': courses})

@api_bp.route('/course/<int:course_id>', methods=['GET'])
@api_login_required
def get_course(course_id):
    """Get course details API endpoint"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user has access to this course
    if current_user.role.name == 'STUDENT' and course not in current_user.courses_enrolled:
        return jsonify({'error': 'Access denied'}), 403
    
    if current_user.role.name == 'TEACHER' and course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get course details
    course_data = to_dict(course, exclude=['created_at', 'updated_at'])
    
    # Get modules and lessons
    modules = []
    for module in course.modules:
        module_data = to_dict(module)
        
        # Get lessons for this module
        lessons = []
        for lesson in module.lessons:
            lessons.append(to_dict(lesson, exclude=['content', 'file_path']))
        
        module_data['lessons'] = lessons
        modules.append(module_data)
    
    course_data['modules'] = modules
    
    return jsonify(course_data)

@api_bp.route('/lesson/<int:lesson_id>', methods=['GET'])
@api_login_required
def get_lesson(lesson_id):
    """Get lesson details API endpoint"""
    lesson = Lesson.query.get_or_404(lesson_id)
    module = lesson.module
    course = module.course
    
    # Check if user has access to this lesson
    if current_user.role.name == 'STUDENT' and course not in current_user.courses_enrolled:
        return jsonify({'error': 'Access denied'}), 403
    
    if current_user.role.name == 'TEACHER' and course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get lesson details
    lesson_data = to_dict(lesson)
    
    return jsonify(lesson_data)

@api_bp.route('/assignments', methods=['GET'])
@api_login_required
def get_assignments():
    """Get assignments API endpoint"""
    assignments = []
    
    if current_user.role.name == 'STUDENT':
        # Get assignments from enrolled courses
        course_ids = [course.id for course in current_user.courses_enrolled]
        query = Assignment.query.filter(Assignment.course_id.in_(course_ids))
        
        for assignment in query.all():
            assignment_data = to_dict(assignment)
            
            # Check if student has submitted
            submission = Submission.query.filter_by(
                assignment_id=assignment.id,
                student_id=current_user.id
            ).first()
            
            assignment_data['submitted'] = submission is not None
            assignment_data['graded'] = submission.grade is not None if submission else False
            
            assignments.append(assignment_data)
    
    elif current_user.role.name == 'TEACHER':
        # Get assignments from courses taught by teacher
        course_ids = [course.id for course in Course.query.filter_by(teacher_id=current_user.id).all()]
        query = Assignment.query.filter(Assignment.course_id.in_(course_ids))
        
        for assignment in query.all():
            assignment_data = to_dict(assignment)
            
            # Get submission count
            submission_count = Submission.query.filter_by(assignment_id=assignment.id).count()
            assignment_data['submission_count'] = submission_count
            
            assignments.append(assignment_data)
    
    return jsonify({'assignments': assignments})

@api_bp.route('/assignment/<int:assignment_id>/submissions', methods=['GET'])
@api_login_required
def get_submissions(assignment_id):
    """Get submissions for assignment API endpoint"""
    assignment = Assignment.query.get_or_404(assignment_id)
    course = assignment.course
    
    # Check if user has access to this assignment
    if current_user.role.name == 'STUDENT' and course not in current_user.courses_enrolled:
        return jsonify({'error': 'Access denied'}), 403
    
    if current_user.role.name == 'TEACHER' and course.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get submissions
    submissions = []
    
    if current_user.role.name == 'STUDENT':
        # Get only student's submission
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first()
        
        if submission:
            submission_data = to_dict(submission, exclude=['content', 'file_path'])
            submissions.append(submission_data)
    
    elif current_user.role.name == 'TEACHER':
        # Get all submissions
        for submission in Submission.query.filter_by(assignment_id=assignment_id).all():
            submission_data = to_dict(submission, exclude=['content', 'file_path'])
            
            # Add student info
            student = User.query.get(submission.student_id)
            submission_data['student'] = {
                'id': student.id,
                'username': student.username,
                'first_name': student.first_name,
                'last_name': student.last_name
            }
            
            submissions.append(submission_data)
    
    return jsonify({'submissions': submissions})

@api_bp.route('/chatbot/sessions', methods=['GET'])
@api_login_required
def get_chat_sessions():
    """Get chat sessions API endpoint"""
    sessions = []
    
    for session in ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.created_at.desc()).all():
        session_data = to_dict(session)
        sessions.append(session_data)
    
    return jsonify({'sessions': sessions})

@api_bp.route('/chatbot/session/<int:session_id>/messages', methods=['GET'])
@api_login_required
def get_chat_messages(session_id):
    """Get chat messages API endpoint"""
    session = ChatSession.query.get_or_404(session_id)
    
    # Ensure the session belongs to the current user
    if session.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    messages = []
    
    for message in session.messages:
        message_data = to_dict(message)
        messages.append(message_data)
    
    return jsonify({'messages': messages})

@api_bp.route('/user/profile', methods=['GET'])
@api_login_required
def get_user_profile():
    """Get user profile API endpoint"""
    user_data = to_dict(current_user, exclude=['password', 'two_factor_secret'])
    
    return jsonify(user_data) 