from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from database.config import db
from database.model import Notification

notifications = Blueprint('notifications', __name__, url_prefix='/notifications')

# Lấy danh sách thông báo của user
@notifications.route('/', methods=['GET'])
@login_required
def list_notifications():
    # Lấy danh sách thông báo
    pass

# Đánh dấu đã đọc
@notifications.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    # Đánh dấu thông báo đã đọc
    pass

# Gửi thông báo (admin/teacher)
@notifications.route('/send', methods=['POST'])
@login_required
def send_notification():
    # Gửi thông báo
    pass

# Xóa thông báo
@notifications.route('/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    # Xóa thông báo
    pass 