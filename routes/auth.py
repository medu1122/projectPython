from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db, bcrypt
from models import User, UserRole
from forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
import pyotp
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # Check if 2FA is enabled for this user
            if user.two_factor_enabled:
                session['user_id'] = user.id
                return redirect(url_for('auth.two_factor_auth'))
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log the user in
            login_user(user, remember=form.remember.data)
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    
    return render_template('login.html', title='Login', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=UserRole.STUDENT  # Default role is student
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', title='Register', form=form)

@auth_bp.route('/logout')
def logout():
    """User logout route"""
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    from forms import UpdateProfileForm
    
    form = UpdateProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.bio = form.bio.data
        
        # Handle profile image upload
        if form.profile_image.data:
            from werkzeug.utils import secure_filename
            import os
            from app import app
            
            filename = secure_filename(form.profile_image.data.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_images', filename)
            form.profile_image.data.save(file_path)
            current_user.profile_image = filename
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.bio.data = current_user.bio
    
    return render_template('profile.html', title='Profile', form=form)

@auth_bp.route('/two-factor-auth', methods=['GET', 'POST'])
def two_factor_auth():
    """Two-factor authentication route"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        otp = request.form.get('otp')
        totp = pyotp.TOTP(user.two_factor_secret)
        
        if totp.verify(otp):
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log the user in
            login_user(user)
            
            # Clear the session
            session.pop('user_id', None)
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('two_factor_auth.html', title='Two-Factor Authentication')

@auth_bp.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    """Request password reset route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Send password reset email (implementation in separate function)
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password_request.html', title='Reset Password', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', title='Reset Password', form=form)

# Helper function for password reset
def send_password_reset_email(user):
    """Send password reset email to user"""
    from flask_mail import Message
    from app import mail
    from flask import current_app
    import jwt
    from datetime import datetime, timedelta
    
    token = jwt.encode(
        {
            'reset_password': user.id,
            'exp': datetime.utcnow() + timedelta(minutes=30)
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    msg = Message(
        'Password Reset Request',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email]
    )
    
    msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_password', token=token, _external=True)}

If you did not make this request, simply ignore this email and no changes will be made.
'''
    
    mail.send(msg) 