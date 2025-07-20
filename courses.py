from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from database.config import db
from database.model import Course, Category, UserCourse, User, Module

courses = Blueprint('courses', __name__, url_prefix='/courses')

@courses.route('/')
def index():
    """Hiển thị danh sách tất cả courses"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    level = request.args.get('level')
    
    # Build query with filters
    query = Course.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if level:
        query = query.filter_by(level=level)
    
    # Paginate results
    pagination = query.order_by(Course.created_at.desc()).paginate(
        page=page, per_page=9, error_out=False
    )
    courses_list = pagination.items
    
    # Get categories for filtering
    categories = Category.query.all()
    levels = ['beginner', 'intermediate', 'advanced']
    
    return render_template(
        'courses/index.html',
        courses=courses_list,
        categories=categories,
        levels=levels,
        pagination=pagination,
        current_category=category_id,
        current_level=level
    )

@courses.route('/<int:course_id>')
def detail(course_id):
    """Hiển thị chi tiết course"""
    course = Course.query.get_or_404(course_id)
    
    # Check if current user is enrolled
    enrollment = None
    if current_user.is_authenticated:
        enrollment = UserCourse.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
    
    return render_template(
        'courses/detail.html',
        course=course,
        enrollment=enrollment
    )

@courses.route('/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    """Đăng ký khóa học"""
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing_enrollment = UserCourse.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        flash('You are already enrolled in this course!', 'warning')
        return redirect(url_for('courses.detail', course_id=course_id))
    
    # Create enrollment
    enrollment = UserCourse(
        user_id=current_user.id,
        course_id=course_id,
        progress=0.0
    )
    
    try:
        db.session.add(enrollment)
        db.session.commit()
        flash(f'Successfully enrolled in {course.name}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during enrollment.', 'danger')
    
    return redirect(url_for('courses.detail', course_id=course_id))

@courses.route('/my-courses')
@login_required  
def my_courses():
    """Danh sách courses của user hiện tại"""
    if current_user.role == 'teacher':
        # Teacher xem courses mình dạy
        taught_courses = Course.query.filter_by(
            teacher_id=current_user.id,
            is_active=True
        ).all()
        return render_template('courses/my_courses_teacher.html', courses=taught_courses)
    
    else:
        # Student xem courses đã đăng ký
        enrollments = UserCourse.query.filter_by(user_id=current_user.id).all()
        return render_template('courses/my_courses_student.html', enrollments=enrollments)

@courses.route('/manage')
@login_required
def manage():
    """Course management cho teachers/admins"""
    if current_user.role not in ['teacher', 'admin']:
        abort(403)
    
    if current_user.role == 'admin':
        # Admin xem tất cả courses
        courses_list = Course.query.all()
    else:
        # Teacher chỉ xem courses của mình
        courses_list = Course.query.filter_by(teacher_id=current_user.id).all()
    
    return render_template('courses/manage.html', courses=courses_list)

@courses.route('/<int:course_id>/students')
@login_required
def course_students(course_id):
    """Xem danh sách students trong course (cho teachers)"""
    course = Course.query.get_or_404(course_id)
    
    # Check permission
    if current_user.role not in ['admin'] and course.teacher_id != current_user.id:
        abort(403)
    
    enrollments = UserCourse.query.filter_by(course_id=course_id).all()
    
    return render_template(
        'courses/students.html',
        course=course,
        enrollments=enrollments
    )

@courses.route('/courses', methods=['GET'])
def get_courses():
    courses = Course.query.all()
    return jsonify([{'id': c.id, 'title': c.title, 'description': c.description} for c in courses])

@courses.route('/courses/<int:course_id>', methods=['GET'])
def get_course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return jsonify({'id': course.id, 'title': course.title, 'description': course.description})

@courses.route('/courses', methods=['POST'])
def create_course():
    data = request.json
    course = Course(title=data['title'], description=data.get('description'))
    db.session.add(course)
    db.session.commit()
    return jsonify({'id': course.id, 'title': course.title}), 201

@courses.route('/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    course = Course.query.get_or_404(course_id)
    data = request.json
    course.title = data.get('title', course.title)
    course.description = data.get('description', course.description)
    db.session.commit()
    return jsonify({'id': course.id, 'title': course.title})

@courses.route('/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    return '', 204

@courses.route('/courses/<int:course_id>/enroll', methods=['POST'])
def enroll_course(course_id):
    user_id = request.json.get('user_id')
    uc = UserCourse(user_id=user_id, course_id=course_id)
    db.session.add(uc)
    db.session.commit()
    return jsonify({'message': 'Enrolled successfully'})

@courses.route('/courses/<int:course_id>/modules', methods=['GET'])
def get_course_modules(course_id):
    modules = Module.query.filter_by(course_id=course_id).all()
    return jsonify([{'id': m.id, 'title': m.title} for m in modules])

@courses.route('/create', methods=['GET', 'POST'])
@login_required
def create_course_form():
    """Form tạo course cho teacher/admin"""
    if current_user.role not in ['teacher', 'admin']:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id', type=int)
        level = request.form.get('level')
        
        if not title or not category_id or not level:
            flash('Vui lòng nhập đầy đủ thông tin.', 'warning')
            return redirect(url_for('courses.create_course_form'))
        
        course = Course(
            title=title,
            description=description,
            category_id=category_id,
            level=level,
            teacher_id=current_user.id,
            is_active=True
        )
        try:
            db.session.add(course)
            db.session.commit()
            flash('Tạo khóa học thành công!', 'success')
            return redirect(url_for('courses.manage'))
        except Exception as e:
            db.session.rollback()
            flash('Có lỗi khi tạo khóa học.', 'danger')
            return redirect(url_for('courses.create_course_form'))
    
    categories = Category.query.all()
    levels = ['beginner', 'intermediate', 'advanced']
    return render_template('courses/create.html', categories=categories, levels=levels)

@courses.route('/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    # Chỉ teacher là chủ course hoặc admin mới được sửa
    if current_user.role == 'teacher' and course.teacher_id != current_user.id:
        abort(403)
    if current_user.role not in ['teacher', 'admin']:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id', type=int)
        level = request.form.get('level')
        
        if not title or not category_id or not level:
            flash('Vui lòng nhập đầy đủ thông tin.', 'warning')
            return redirect(url_for('courses.edit_course', course_id=course_id))
        
        course.title = title
        course.description = description
        course.category_id = category_id
        course.level = level
        try:
            db.session.commit()
            flash('Cập nhật khóa học thành công!', 'success')
            return redirect(url_for('courses.manage'))
        except Exception as e:
            db.session.rollback()
            flash('Có lỗi khi cập nhật khóa học.', 'danger')
            return redirect(url_for('courses.edit_course', course_id=course_id))
    
    categories = Category.query.all()
    levels = ['beginner', 'intermediate', 'advanced']
    return render_template('courses/edit.html', course=course, categories=categories, levels=levels) 
    
