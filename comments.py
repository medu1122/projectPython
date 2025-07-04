from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from database.config import db
from database.model import Comment

comments = Blueprint('comments', __name__, url_prefix='/comments')

# Thêm comment cho lesson
@comments.route('/lesson/<int:lesson_id>/add', methods=['POST'])
@login_required
def add_comment_lesson(lesson_id):
    # Thêm comment cho lesson
    pass

# Thêm comment cho assignment
@comments.route('/assignment/<int:assignment_id>/add', methods=['POST'])
@login_required
def add_comment_assignment(assignment_id):
    # Thêm comment cho assignment
    pass

# Lấy danh sách comment cho lesson
@comments.route('/lesson/<int:lesson_id>', methods=['GET'])
@login_required
def list_comments_lesson(lesson_id):
    # Lấy danh sách comment cho lesson
    pass

# Lấy danh sách comment cho assignment
@comments.route('/assignment/<int:assignment_id>', methods=['GET'])
@login_required
def list_comments_assignment(assignment_id):
    # Lấy danh sách comment cho assignment
    pass

# Xóa comment
@comments.route('/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    # Xóa comment (chỉ owner hoặc admin)
    pass

# Sửa comment
@comments.route('/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    # Sửa comment (chỉ owner)
    pass 