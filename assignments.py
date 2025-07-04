from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from database.config import db
from database.model import Assignment, Lesson, AssignmentSubmission, User
from datetime import datetime

assignments = Blueprint('assignments', __name__, url_prefix='/assignments')

# CRUD Assignment (teacher/admin)
@assignments.route('/lesson/<int:lesson_id>', methods=['GET'])
@login_required
def get_assignments_by_lesson(lesson_id):
    # Lấy danh sách assignment theo lesson
    pass

@assignments.route('/<int:assignment_id>', methods=['GET'])
@login_required
def view_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    submission = None
    if current_user.role == 'student':
        submission = AssignmentSubmission.query.filter_by(
            assignment_id=assignment_id, user_id=current_user.id
        ).first()
    return render_template('assignments/view.html', assignment=assignment, submission=submission)

@assignments.route('/lesson/<int:lesson_id>/create', methods=['GET', 'POST'])
@login_required
def create_assignment(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if current_user.role != 'teacher':
        abort(403)
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        type_ = request.form.get('type', 'essay')
        due_date = request.form.get('due_date')
        max_score = request.form.get('max_score', type=float)
        assignment = Assignment(
            lesson_id=lesson_id,
            title=title,
            description=description,
            type=type_,
            due_date=due_date,
            max_score=max_score or 100.0
        )
        db.session.add(assignment)
        db.session.commit()
        flash('Tạo assignment thành công!', 'success')
        return redirect(url_for('lessons.view_lesson', lesson_id=lesson_id))
    return render_template('assignments/create.html', lesson=lesson)

@assignments.route('/<int:assignment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_assignment(assignment_id):
    # Sửa assignment
    pass

@assignments.route('/<int:assignment_id>/delete', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    # Xóa assignment
    pass

# Student nộp bài assignment (text)
@assignments.route('/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    if current_user.role != 'student':
        abort(403)
    submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id, user_id=current_user.id
    ).first()
    if request.method == 'POST':
        content = request.form.get('content')
        if not submission:
            submission = AssignmentSubmission(
                assignment_id=assignment_id,
                user_id=current_user.id,
                content=content
            )
            db.session.add(submission)
        else:
            submission.content = content
            submission.submitted_at = datetime.now()
        db.session.commit()
        flash('Đã nộp bài thành công!', 'success')
        return redirect(url_for('assignments.view_assignment', assignment_id=assignment_id))
    return render_template('assignments/submit.html', assignment=assignment, submission=submission)

# Teacher xem và chấm điểm submission
@assignments.route('/submission/<int:submission_id>/grade', methods=['GET', 'POST'])
@login_required
def grade_submission(submission_id):
    submission = AssignmentSubmission.query.get_or_404(submission_id)
    assignment = submission.assignment
    if current_user.role != 'teacher':
        abort(403)
    if request.method == 'POST':
        score = request.form.get('score', type=float)
        submission.score = score
        db.session.commit()
        flash('Đã chấm điểm!', 'success')
        return redirect(url_for('assignments.view_assignment', assignment_id=assignment.id))
    return render_template('assignments/grade.html', submission=submission, assignment=assignment)

# Feedback cho submission
@assignments.route('/submission/<int:submission_id>/feedback', methods=['GET', 'POST'])
@login_required
def feedback_submission(submission_id):
    # Gửi feedback cho bài nộp
    pass

# Download/upload file cho assignment/submission
@assignments.route('/<int:assignment_id>/download', methods=['GET'])
@login_required
def download_assignment_file(assignment_id):
    # Download file assignment
    pass

@assignments.route('/<int:assignment_id>/upload', methods=['POST'])
@login_required
def upload_assignment_file(assignment_id):
    # Upload file cho assignment
    pass

@assignments.route('/submission/<int:submission_id>/download', methods=['GET'])
@login_required
def download_submission_file(submission_id):
    # Download file bài nộp
    pass

@assignments.route('/submission/<int:submission_id>/upload', methods=['POST'])
@login_required
def upload_submission_file(submission_id):
    # Upload file cho bài nộp
    pass 