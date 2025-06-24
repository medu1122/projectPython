from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from database.config import db
from database.model import User
from forms import RegistrationForm
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Create new user
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        
        new_user = User(
            name=form.username.data,
            email=form.email.data,
            password=hashed_password,
            role=form.role.data,
            create_at=datetime.now(),
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
    # Placeholder for login route
    return render_template('login.html', title='Login') 