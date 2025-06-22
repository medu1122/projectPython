from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from models import Course, User, UserRole

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page route"""
    if current_user.is_authenticated:
        if current_user.role == UserRole.STUDENT:
            return redirect(url_for('student.dashboard'))
        elif current_user.role == UserRole.TEACHER:
            return redirect(url_for('teacher.dashboard'))
        elif current_user.role == UserRole.ADMIN:
            return redirect(url_for('admin.dashboard'))
    
    # Get featured courses for homepage
    featured_courses = Course.query.filter_by(is_active=True).limit(6).all()
    
    return render_template('index.html', featured_courses=featured_courses)

@main_bp.route('/about')
def about():
    """About page route"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page route"""
    return render_template('contact.html')

@main_bp.route('/courses')
def courses():
    """All courses page route"""
    page = request.args.get('page', 1, type=int)
    courses = Course.query.filter_by(is_active=True).paginate(page=page, per_page=12)
    return render_template('courses.html', courses=courses)

@main_bp.route('/course/<string:code>')
def course_details(code):
    """Course details page route"""
    course = Course.query.filter_by(code=code).first_or_404()
    
    # Check if user is enrolled
    is_enrolled = False
    if current_user.is_authenticated and current_user.role == UserRole.STUDENT:
        is_enrolled = course in current_user.courses_enrolled
    
    return render_template('course_details.html', course=course, is_enrolled=is_enrolled) 