from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from database.config import db

admin = Blueprint('admin', __name__, url_prefix='/admin')

# Dashboard admin
@admin.route('/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    # Trang dashboard admin
    pass

# Báo cáo thống kê
@admin.route('/reports', methods=['GET'])
@login_required
def admin_reports():
    # Trang báo cáo thống kê
    pass

# Quản lý user
@admin.route('/users', methods=['GET'])
@login_required
def manage_users():
    # Quản lý user
    pass

# Quản lý khóa học
@admin.route('/courses', methods=['GET'])
@login_required
def manage_courses():
    # Quản lý khóa học
    pass

# Quản lý lesson
@admin.route('/lessons', methods=['GET'])
@login_required
def manage_lessons():
    # Quản lý lesson
    pass

# Quản lý assignment
@admin.route('/assignments', methods=['GET'])
@login_required
def manage_assignments():
    # Quản lý assignment
    pass

# Quản lý certificate
@admin.route('/certificates', methods=['GET'])
@login_required
def manage_certificates():
    # Quản lý certificate
    pass

# Quản lý payment
@admin.route('/payments', methods=['GET'])
@login_required
def manage_payments():
    # Quản lý payment
    pass 