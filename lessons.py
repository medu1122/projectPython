from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from database.config import db
from database.model import Course, Module, Lesson, LessonContent, UserProgress, UserCourse
from datetime import datetime

lessons = Blueprint('lessons', __name__, url_prefix='/lessons')

@lessons.route('/course/<int:course_id>')
@login_required
def course_curriculum(course_id):
    """Hiển thị curriculum của course"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled
    enrollment = UserCourse.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment and current_user.role == 'student':
        flash('You need to enroll in this course first.', 'warning')
        return redirect(url_for('courses.detail', course_id=course_id))
    
    # Get user progress for each lesson
    user_progress = {}
    if current_user.role == 'student':
        progress_records = UserProgress.query.filter_by(user_id=current_user.id).all()
        user_progress = {p.lesson_id: p for p in progress_records}
    
    return render_template(
        'lessons/curriculum.html',
        course=course,
        enrollment=enrollment,
        user_progress=user_progress
    )

@lessons.route('/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    """Xem nội dung lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.module.course
    
    # Check access permission
    if current_user.role == 'student':
        enrollment = UserCourse.query.filter_by(
            user_id=current_user.id,
            course_id=course.id
        ).first()
        
        if not enrollment:
            abort(403)
    elif current_user.role == 'teacher':
        if course.teacher_id != current_user.id:
            abort(403)
    
    # Get or create user progress
    user_progress = None
    if current_user.role == 'student':
        user_progress = UserProgress.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson_id
        ).first()
        
        if not user_progress:
            user_progress = UserProgress(
                user_id=current_user.id,
                lesson_id=lesson_id
            )
            db.session.add(user_progress)
            db.session.commit()
    
    # Get navigation info (previous/next lessons)
    all_lessons = []
    for module in course.modules:
        all_lessons.extend(module.lessons)
    
    current_index = next((i for i, l in enumerate(all_lessons) if l.id == lesson_id), None)
    prev_lesson = all_lessons[current_index - 1] if current_index and current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if current_index is not None and current_index < len(all_lessons) - 1 else None
    
    return render_template(
        'lessons/view.html',
        lesson=lesson,
        course=course,
        user_progress=user_progress,
        prev_lesson=prev_lesson,
        next_lesson=next_lesson
    )

@lessons.route('/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(lesson_id):
    """Mark lesson as completed"""
    if current_user.role != 'student':
        abort(403)
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Get or create progress record
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            lesson_id=lesson_id
        )
        db.session.add(progress)
    
    # Mark as completed
    progress.mark_completed()
    
    # Update course progress
    course_id = lesson.module.course_id
    enrollment = UserCourse.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if enrollment:
        new_progress = lesson.module.course.get_user_progress(current_user.id)
        enrollment.progress = new_progress
    
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Lesson completed!',
            'progress': enrollment.progress if enrollment else 0
        })
    
    flash('Lesson completed! Great job!', 'success')
    return redirect(url_for('lessons.view_lesson', lesson_id=lesson_id))

@lessons.route('/course/<int:course_id>/progress')
@login_required
def course_progress(course_id):
    """API endpoint để lấy progress của course"""
    if current_user.role != 'student':
        abort(403)
    
    course = Course.query.get_or_404(course_id)
    progress = course.get_user_progress(current_user.id)
    
    return jsonify({
        'course_id': course_id,
        'progress': progress,
        'total_lessons': course.total_lessons
    })

# Admin/Teacher routes for content management
@lessons.route('/course/<int:course_id>/manage')
@login_required
def manage_course_content(course_id):
    """Manage course content (for teachers/admins)"""
    course = Course.query.get_or_404(course_id)
    
    # Check permission
    if current_user.role == 'teacher' and course.teacher_id != current_user.id:
        abort(403)
    elif current_user.role not in ['teacher', 'admin']:
        abort(403)
    
    return render_template(
        'lessons/manage.html',
        course=course
    )

@lessons.route('/module/<int:module_id>/add-lesson', methods=['GET', 'POST'])
@login_required
def add_lesson(module_id):
    """Add new lesson to module"""
    module = Module.query.get_or_404(module_id)
    
    # Check permission
    if current_user.role == 'teacher' and module.course.teacher_id != current_user.id:
        abort(403)
    elif current_user.role not in ['teacher', 'admin']:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        lesson_type = request.form.get('lesson_type')
        duration = request.form.get('duration_minutes', type=int)
        
        # Get next order index
        max_order = db.session.query(db.func.max(Lesson.order_index)).filter_by(module_id=module_id).scalar() or 0
        
        lesson = Lesson(
            title=title,
            description=description,
            module_id=module_id,
            lesson_type=lesson_type,
            duration_minutes=duration,
            order_index=max_order + 1
        )
        
        db.session.add(lesson)
        db.session.commit()
        
        flash(f'Lesson "{title}" created successfully!', 'success')
        return redirect(url_for('lessons.manage_course_content', course_id=module.course_id))
    
    return render_template('lessons/add_lesson.html', module=module) 