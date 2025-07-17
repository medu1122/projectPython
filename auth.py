from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from database.config import db
from database.model import User
from forms import RegistrationForm, LoginForm
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Create new user
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        
        new_user = User(
            name=f"{form.first_name.data} {form.last_name.data}",  # Combine first and last name
            email=form.email.data,
            password=hashed_password,
            role=form.role.data,
            created_at=datetime.now(),
            is_active=True
        )
        
        try:
            # Add to database
            db.session.add(new_user)
            db.session.commit()
            
            # Success message
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    # If GET request or form validation failed
    return render_template('register.html', form=form, title='Register')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect_user_by_role(current_user.role)
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Find user by email
        user = User.query.filter_by(email=form.email.data).first()
        
        # Check if user exists and password is correct
        if user and check_password_hash(user.password, form.password.data):
            # Check if user is active
            if user.is_active:
                # Login user
                login_user(user, remember=form.remember_me.data)
                flash(f'Welcome back, {user.name}!', 'success')
                
                # Redirect to appropriate dashboard based on role
                return redirect_user_by_role(user.role)
            else:
                flash('Your account has been deactivated. Please contact support.', 'warning')
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html', form=form, title='Login')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

def redirect_user_by_role(role):
    """Redirect user to appropriate dashboard based on their role"""
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    else:  # student or any other role
        return redirect(url_for('student_dashboard')) 
@auth.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    #xử lý cập nhật thông tin
    fullname=request.form.get('fullname')
    phone=request.form.get('phone')
    bio=request.form.get('bio')
    #cap nhat thong tin cho curent_user
    current_user.fullname=fullname
    current_user.phone=phone
    current_user.bio=bio

    try:
        db.session.commit()
        flash('Your profile has been updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi cập nhật hồ sơ: {str(e)}', 'danger')
    return redirect(url_for('profile'))
