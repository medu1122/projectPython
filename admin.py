from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, abort, send_file
from flask_login import login_required, current_user
from database.config import db
from database.model import User

admin = Blueprint('admin', __name__, url_prefix='/admin')

# Dashboard admin
@admin.route('/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    # Trang dashboard admin
    return render_template('admin/dashboard.html')

# Báo cáo thống kê
@admin.route('/reports', methods=['GET'])
@login_required
def admin_reports():
    # Trang báo cáo thống kê
    return render_template('admin/reports.html')

# Quản lý user
@admin.route('/users', methods=['GET'])
@login_required
def manage_users():
    """Quản lý danh sách người dùng với phân trang và tìm kiếm"""
    if current_user.role != 'admin':
        flash('Permission denied!', 'danger')
        return redirect(url_for('index'))
    
    # Lấy tham số tìm kiếm và phân trang
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    # Query cơ bản
    query = User.query
    
    # Áp dụng filter tìm kiếm
    if search:
        query = query.filter(
            db.or_(
                User.name.contains(search),
                User.email.contains(search)
            )
        )
    
    # Filter theo vai trò
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    # Filter theo trạng thái
    if status_filter:
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
    
    # Phân trang
    per_page = 10
    # Thêm ORDER BY để tránh lỗi MSSQL
    query = query.order_by(User.id)
    users = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Thống kê
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    
    stats = {
        'total': total_users,
        'active': active_users,
        'inactive': inactive_users,
        'students': User.query.filter_by(role='student').count(),
        'teachers': User.query.filter_by(role='teacher').count(),
        'admins': User.query.filter_by(role='admin').count()
    }
    
    return render_template('admin/users.html', 
                         users=users,
                         search=search,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         stats=stats)

# Quản lý khóa học
@admin.route('/courses', methods=['GET'])
@login_required
def manage_courses():
    # Quản lý khóa học
    return render_template('admin/courses.html')

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
    return render_template('admin/payments.html')

# Thay đổi vai trò người dùng
@admin.route('/users/<int:user_id>/change-role', methods=['POST'])
@login_required
def change_user_role(user_id):
    """Thay đổi vai trò người dùng"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Permission denied!'}), 403
    
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role not in ['student', 'teacher', 'admin']:
        return jsonify({'success': False, 'message': 'Invalid role!'}), 400
    
    # Không cho phép thay đổi vai trò của chính mình
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot change your own role!'}), 400
    
    old_role = user.role
    user.role = new_role
    
    try:
        db.session.commit()
        flash(f'Đã thay đổi vai trò của {user.name} từ {old_role} thành {new_role}', 'success')
        return jsonify({'success': True, 'message': 'Role changed successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Khóa/Mở khóa tài khoản
@admin.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Khóa hoặc mở khóa tài khoản người dùng"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Permission denied!'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Không cho phép khóa tài khoản của chính mình
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot deactivate your own account!'}), 400
    
    user.is_active = not user.is_active
    status = 'activated' if user.is_active else 'deactivated'
    
    try:
        db.session.commit()
        flash(f'Đã {status} tài khoản của {user.name}', 'success')
        return jsonify({
            'success': True, 
            'message': f'Account {status} successfully!',
            'is_active': user.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Xóa người dùng
@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Xóa người dùng"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Permission denied!'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Không cho phép xóa tài khoản của chính mình
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot delete your own account!'}), 400
    
    user_name = user.name
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'Đã xóa người dùng {user_name}', 'success')
        return jsonify({'success': True, 'message': 'User deleted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Export users to Excel
@admin.route('/users/export', methods=['GET'])
@login_required
def export_users():
    """Xuất danh sách người dùng ra file Excel"""
    if current_user.role != 'admin':
        flash('Permission denied!', 'danger')
        return redirect(url_for('index'))
    
    try:
        import pandas as pd
        from io import BytesIO
        from datetime import datetime
        
        # Lấy tham số filter
        search = request.args.get('search', '')
        role_filter = request.args.get('role', '')
        status_filter = request.args.get('status', '')
        
        # Query users
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.name.contains(search),
                    User.email.contains(search)
                )
            )
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        if status_filter:
            if status_filter == 'active':
                query = query.filter(User.is_active == True)
            elif status_filter == 'inactive':
                query = query.filter(User.is_active == False)
        
        users = query.all()
        
        # Tạo DataFrame
        data = []
        for user in users:
            data.append({
                'ID': user.id,
                'Tên': user.name,
                'Email': user.email,
                'Vai trò': user.role,
                'Trạng thái': 'Đang hoạt động' if user.is_active else 'Đã khóa',
                'Ngày tạo': user.created_at.strftime('%d/%m/%Y %H:%M') if user.created_at else ''
            })
        
        df = pd.DataFrame(data)
        
        # Tạo file Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Users', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Users']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        # Tạo tên file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'users_export_{timestamp}.xlsx'
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except ImportError:
        flash('Cần cài đặt pandas để xuất Excel!', 'warning')
        return redirect(url_for('admin.manage_users'))
    except Exception as e:
        flash(f'Lỗi khi xuất file: {str(e)}', 'danger')
        return redirect(url_for('admin.manage_users')) 