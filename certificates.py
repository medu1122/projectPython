from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from database.config import db
from database.model import Certificate

certificates = Blueprint('certificates', __name__, url_prefix='/certificates')

# Cấp chứng chỉ cho user (admin/teacher)
@certificates.route('/issue', methods=['POST'])
@login_required
def issue_certificate():
    # Cấp chứng chỉ cho user
    pass

# Lấy danh sách chứng chỉ của user
@certificates.route('/user/<int:user_id>', methods=['GET'])
@login_required
def list_certificates(user_id):
    # Lấy danh sách chứng chỉ
    pass

# Xem chi tiết chứng chỉ
@certificates.route('/<int:certificate_id>', methods=['GET'])
@login_required
def view_certificate(certificate_id):
    # Xem chi tiết chứng chỉ
    pass

# Tải chứng chỉ PDF
@certificates.route('/<int:certificate_id>/download', methods=['GET'])
@login_required
def download_certificate(certificate_id):
    # Tải chứng chỉ PDF
    pass 