from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app import db, bcrypt
from models import User, Course, UserRole
from functools import wraps
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# Custom decorator to ensure user is an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash('Access denied. You must be an administrator to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard route"""
    # Get system statistics
    user_count = User.query.count()
    student_count = User.query.filter_by(role=UserRole.STUDENT).count()
    teacher_count = User.query.filter_by(role=UserRole.TEACHER).count()
    course_count = Course.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.date_joined.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                          user_count=user_count,
                          student_count=student_count,
                          teacher_count=teacher_count,
                          course_count=course_count,
                          recent_users=recent_users)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management route"""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_details(user_id):
    """User details route"""
    user = User.query.get_or_404(user_id)
    
    # Get courses for student or teacher
    if user.role == UserRole.STUDENT:
        courses = user.courses_enrolled
    elif user.role == UserRole.TEACHER:
        courses = user.courses_teaching
    else:
        courses = []
    
    return render_template('admin/user_details.html', user=user, courses=courses)

@admin_bp.route('/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create new user route"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        
        # Validate inputs
        if not username or not email or not password or not first_name or not last_name or not role:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.new_user'))
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.new_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.new_user'))
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            username=username,
            email=email,
            password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=UserRole(role)
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {username} has been created successfully.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/new_user.html')

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user route"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        is_active = 'is_active' in request.form
        
        # Validate inputs
        if not username or not email or not first_name or not last_name or not role:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))
        
        # Check if username already exists (for another user)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))
        
        # Check if email already exists (for another user)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))
        
        # Update user
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.role = UserRole(role)
        user.is_active = is_active
        
        # Update password if provided
        new_password = request.form.get('password')
        if new_password:
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        
        db.session.commit()
        
        flash(f'User {username} has been updated successfully.', 'success')
        return redirect(url_for('admin.user_details', user_id=user.id))
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user route"""
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/courses')
@login_required
@admin_required
def courses():
    """Course management route"""
    page = request.args.get('page', 1, type=int)
    courses = Course.query.paginate(page=page, per_page=10)
    
    return render_template('admin/courses.html', courses=courses)

@admin_bp.route('/course/<int:course_id>')
@login_required
@admin_required
def course_details(course_id):
    """Course details route"""
    course = Course.query.get_or_404(course_id)
    teacher = User.query.get(course.teacher_id)
    students = course.students.all()
    
    return render_template('admin/course_details.html', 
                          course=course,
                          teacher=teacher,
                          students=students)

@admin_bp.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    """Edit course route"""
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        code = request.form.get('code')
        teacher_id = request.form.get('teacher_id')
        is_active = 'is_active' in request.form
        
        # Validate inputs
        if not title or not code or not teacher_id:
            flash('Title, code, and teacher are required.', 'danger')
            return redirect(url_for('admin.edit_course', course_id=course.id))
        
        # Check if course code already exists (for another course)
        existing_course = Course.query.filter_by(code=code).first()
        if existing_course and existing_course.id != course.id:
            flash('Course code already exists.', 'danger')
            return redirect(url_for('admin.edit_course', course_id=course.id))
        
        # Check if teacher exists
        teacher = User.query.get(teacher_id)
        if not teacher or teacher.role != UserRole.TEACHER:
            flash('Invalid teacher selected.', 'danger')
            return redirect(url_for('admin.edit_course', course_id=course.id))
        
        # Update course
        course.title = title
        course.description = description
        course.code = code
        course.teacher_id = teacher_id
        course.is_active = is_active
        course.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Course {title} has been updated successfully.', 'success')
        return redirect(url_for('admin.course_details', course_id=course.id))
    
    # Get all teachers for dropdown
    teachers = User.query.filter_by(role=UserRole.TEACHER).all()
    
    return render_template('admin/edit_course.html', course=course, teachers=teachers)

@admin_bp.route('/course/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    """Delete course route"""
    course = Course.query.get_or_404(course_id)
    
    db.session.delete(course)
    db.session.commit()
    
    flash(f'Course {course.title} has been deleted.', 'success')
    return redirect(url_for('admin.courses'))

@admin_bp.route('/system-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def system_settings():
    """System settings route"""
    from flask import current_app
    
    if request.method == 'POST':
        # Update settings in database or config file
        # This would depend on how you store your settings
        
        flash('System settings have been updated.', 'success')
        return redirect(url_for('admin.system_settings'))
    
    # Get current settings
    settings = {
        'site_name': current_app.config.get('SITE_NAME', 'Learning Management System'),
        'mail_server': current_app.config.get('MAIL_SERVER'),
        'mail_port': current_app.config.get('MAIL_PORT'),
        'mail_username': current_app.config.get('MAIL_USERNAME'),
        'default_language': current_app.config.get('DEFAULT_LANGUAGE', 'en')
    }
    
    return render_template('admin/system_settings.html', settings=settings) 