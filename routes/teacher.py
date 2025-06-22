from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from models import Course, Module, Lesson, Assignment, Submission, User, UserRole, LessonType
from functools import wraps
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app

teacher_bp = Blueprint('teacher', __name__)

# Custom decorator to ensure user is a teacher
def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.TEACHER:
            flash('Access denied. You must be a teacher to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    """Teacher dashboard route"""
    # Get courses taught by this teacher
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    # Get recent submissions that need grading
    recent_submissions = []
    for course in courses:
        for assignment in course.assignments:
            submissions = Submission.query.filter_by(
                assignment_id=assignment.id,
                grade=None  # Ungraded submissions
            ).order_by(Submission.submitted_at.desc()).all()
            
            for submission in submissions:
                recent_submissions.append({
                    'submission': submission,
                    'student': User.query.get(submission.student_id),
                    'assignment': assignment,
                    'course': course
                })
    
    # Sort by submission date
    recent_submissions.sort(key=lambda x: x['submission'].submitted_at, reverse=True)
    
    # Limit to 10 most recent
    recent_submissions = recent_submissions[:10]
    
    # Get student counts per course
    course_stats = []
    for course in courses:
        student_count = len(course.students.all())
        assignment_count = len(course.assignments)
        course_stats.append({
            'course': course,
            'student_count': student_count,
            'assignment_count': assignment_count
        })
    
    return render_template('teacher/dashboard.html',
                          courses=courses,
                          recent_submissions=recent_submissions,
                          course_stats=course_stats)

@teacher_bp.route('/courses')
@login_required
@teacher_required
def courses():
    """Teacher's courses route"""
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher/courses.html', courses=courses)

@teacher_bp.route('/course/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def new_course():
    """Create new course route"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        code = request.form.get('code')
        
        # Validate inputs
        if not title or not code:
            flash('Title and course code are required.', 'danger')
            return redirect(url_for('teacher.new_course'))
        
        # Check if course code already exists
        existing_course = Course.query.filter_by(code=code).first()
        if existing_course:
            flash('Course code already exists. Please choose a different code.', 'danger')
            return redirect(url_for('teacher.new_course'))
        
        # Create new course
        course = Course(
            title=title,
            description=description,
            code=code,
            teacher_id=current_user.id
        )
        
        # Handle course image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'course_images', filename)
                file.save(file_path)
                course.image = filename
        
        db.session.add(course)
        db.session.commit()
        
        flash(f'Course "{title}" has been created successfully.', 'success')
        return redirect(url_for('teacher.course_content', course_id=course.id))
    
    return render_template('teacher/new_course.html')

@teacher_bp.route('/course/<int:course_id>')
@login_required
@teacher_required
def course_details(course_id):
    """Course details route"""
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You do not have permission to view this course.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    # Get student enrollment data
    students = course.students.all()
    
    return render_template('teacher/course_details.html', 
                          course=course,
                          students=students)

@teacher_bp.route('/course/<int:course_id>/content')
@login_required
@teacher_required
def course_content(course_id):
    """Course content management route"""
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    return render_template('teacher/course_content.html', course=course)

@teacher_bp.route('/course/<int:course_id>/module/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def new_module(course_id):
    """Create new module route"""
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title:
            flash('Module title is required.', 'danger')
            return redirect(url_for('teacher.new_module', course_id=course.id))
        
        # Get the highest order value and increment
        highest_order = db.session.query(db.func.max(Module.order)).filter_by(course_id=course.id).scalar() or 0
        
        module = Module(
            title=title,
            description=description,
            course_id=course.id,
            order=highest_order + 1
        )
        
        db.session.add(module)
        db.session.commit()
        
        flash(f'Module "{title}" has been created successfully.', 'success')
        return redirect(url_for('teacher.course_content', course_id=course.id))
    
    return render_template('teacher/new_module.html', course=course)

@teacher_bp.route('/module/<int:module_id>/lesson/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def new_lesson(module_id):
    """Create new lesson route"""
    module = Module.query.get_or_404(module_id)
    course = module.course
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        lesson_type = request.form.get('lesson_type')
        
        if not title:
            flash('Lesson title is required.', 'danger')
            return redirect(url_for('teacher.new_lesson', module_id=module.id))
        
        # Get the highest order value and increment
        highest_order = db.session.query(db.func.max(Lesson.order)).filter_by(module_id=module.id).scalar() or 0
        
        lesson = Lesson(
            title=title,
            content=content,
            module_id=module.id,
            lesson_type=LessonType(lesson_type),
            order=highest_order + 1
        )
        
        # Handle file upload for PDF, video, etc.
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'lesson_files', filename)
                file.save(file_path)
                lesson.file_path = filename
        
        db.session.add(lesson)
        db.session.commit()
        
        flash(f'Lesson "{title}" has been created successfully.', 'success')
        return redirect(url_for('teacher.course_content', course_id=course.id))
    
    return render_template('teacher/new_lesson.html', module=module, course=course)

@teacher_bp.route('/course/<int:course_id>/assignment/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def new_assignment(course_id):
    """Create new assignment route"""
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        points = request.form.get('points')
        
        if not title or not description:
            flash('Title and description are required.', 'danger')
            return redirect(url_for('teacher.new_assignment', course_id=course.id))
        
        # Parse due date
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid due date format.', 'danger')
                return redirect(url_for('teacher.new_assignment', course_id=course.id))
        
        assignment = Assignment(
            title=title,
            description=description,
            course_id=course.id,
            due_date=due_date_obj,
            points=int(points) if points else 100
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        flash(f'Assignment "{title}" has been created successfully.', 'success')
        return redirect(url_for('teacher.course_assignments', course_id=course.id))
    
    return render_template('teacher/new_assignment.html', course=course)

@teacher_bp.route('/course/<int:course_id>/assignments')
@login_required
@teacher_required
def course_assignments(course_id):
    """Course assignments route"""
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You do not have permission to view this course.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    assignments = Assignment.query.filter_by(course_id=course.id).order_by(Assignment.due_date).all()
    
    return render_template('teacher/course_assignments.html', 
                          course=course,
                          assignments=assignments)

@teacher_bp.route('/assignment/<int:assignment_id>/submissions')
@login_required
@teacher_required
def assignment_submissions(assignment_id):
    """View assignment submissions route"""
    assignment = Assignment.query.get_or_404(assignment_id)
    course = assignment.course
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You do not have permission to view these submissions.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    # Get all submissions for this assignment
    submissions = Submission.query.filter_by(assignment_id=assignment.id).all()
    
    # Add student info to each submission
    submission_data = []
    for submission in submissions:
        student = User.query.get(submission.student_id)
        submission_data.append({
            'submission': submission,
            'student': student
        })
    
    return render_template('teacher/assignment_submissions.html',
                          assignment=assignment,
                          course=course,
                          submissions=submission_data)

@teacher_bp.route('/submission/<int:submission_id>/grade', methods=['GET', 'POST'])
@login_required
@teacher_required
def grade_submission(submission_id):
    """Grade assignment submission route"""
    submission = Submission.query.get_or_404(submission_id)
    assignment = Assignment.query.get(submission.assignment_id)
    course = assignment.course
    student = User.query.get(submission.student_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You do not have permission to grade this submission.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    if request.method == 'POST':
        grade = request.form.get('grade')
        feedback = request.form.get('feedback')
        
        try:
            grade_float = float(grade)
            if grade_float < 0 or grade_float > assignment.points:
                flash(f'Grade must be between 0 and {assignment.points}.', 'danger')
                return redirect(url_for('teacher.grade_submission', submission_id=submission.id))
            
            submission.grade = grade_float
            submission.feedback = feedback
            submission.graded_at = datetime.utcnow()
            submission.graded_by = current_user.id
            
            db.session.commit()
            
            flash('Submission has been graded successfully.', 'success')
            return redirect(url_for('teacher.assignment_submissions', assignment_id=assignment.id))
        
        except ValueError:
            flash('Invalid grade value. Please enter a number.', 'danger')
    
    return render_template('teacher/grade_submission.html',
                          submission=submission,
                          assignment=assignment,
                          course=course,
                          student=student)

@teacher_bp.route('/course/<int:course_id>/students')
@login_required
@teacher_required
def course_students(course_id):
    """View course students route"""
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You do not have permission to view this course.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    # Get all enrolled students
    students = course.students.all()
    
    # Get progress data for each student
    student_data = []
    for student in students:
        # Calculate completion percentage
        total_lessons = sum(len(module.lessons) for module in course.modules)
        
        completed_lessons = db.session.query(LessonCompletion).join(Lesson).join(Module).filter(
            LessonCompletion.user_id == student.id,
            Module.course_id == course.id
        ).count()
        
        progress = 0
        if total_lessons > 0:
            progress = (completed_lessons / total_lessons) * 100
        
        # Get submission data
        assignment_count = len(course.assignments)
        submissions = db.session.query(Submission).join(Assignment).filter(
            Submission.student_id == student.id,
            Assignment.course_id == course.id
        ).all()
        
        submission_count = len(submissions)
        
        # Calculate average grade
        grades = [s.grade for s in submissions if s.grade is not None]
        avg_grade = sum(grades) / len(grades) if grades else None
        
        student_data.append({
            'student': student,
            'progress': progress,
            'submission_count': submission_count,
            'assignment_count': assignment_count,
            'avg_grade': avg_grade
        })
    
    return render_template('teacher/course_students.html',
                          course=course,
                          student_data=student_data)

@teacher_bp.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_course(course_id):
    """Edit course route"""
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You do not have permission to edit this course.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        is_active = 'is_active' in request.form
        
        if not title:
            flash('Course title is required.', 'danger')
            return redirect(url_for('teacher.edit_course', course_id=course.id))
        
        course.title = title
        course.description = description
        course.is_active = is_active
        course.updated_at = datetime.utcnow()
        
        # Handle course image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'course_images', filename)
                file.save(file_path)
                course.image = filename
        
        db.session.commit()
        
        flash('Course has been updated successfully.', 'success')
        return redirect(url_for('teacher.course_details', course_id=course.id))
    
    return render_template('teacher/edit_course.html', course=course) 