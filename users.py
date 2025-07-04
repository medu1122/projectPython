from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from database.config import db
from database.model import User

users = Blueprint('users', __name__, url_prefix='/users')

# Xem profile
@users.route('/<int:user_id>', methods=['GET'])
@login_required
def view_profile(user_id):
    # Xem profile user
    pass

# Cập nhật thông tin cá nhân
@users.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    # Sửa thông tin cá nhân
    pass

# Đổi mật khẩu
@users.route('/<int:user_id>/change-password', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    # Đổi mật khẩu
    pass

# Bật/tắt 2FA
@users.route('/<int:user_id>/2fa', methods=['GET', 'POST'])
@login_required
def manage_2fa(user_id):
    # Bật/tắt 2FA
    pass

# Xem hoạt động gần đây
@users.route('/<int:user_id>/activity', methods=['GET'])
@login_required
def recent_activity(user_id):
    # Xem hoạt động gần đây
    pass

# Lấy danh sách user (admin)
@users.route('/list', methods=['GET'])
@login_required
def list_users():
    # Lấy danh sách user (admin)
    pass

# Xóa user (admin)
@users.route('/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    # Xóa user (admin)
    pass 