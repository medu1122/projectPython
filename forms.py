from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User, Course, UserRole
from flask_login import current_user

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')

class UpdateProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    bio = TextAreaField('Bio')
    profile_image = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class CourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired()])
    description = TextAreaField('Course Description')
    code = StringField('Course Code', validators=[DataRequired()])
    image = FileField('Course Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Create Course')

    def validate_code(self, code):
        course = Course.query.filter_by(code=code.data).first()
        if course:
            raise ValidationError('That course code is already taken. Please choose a different one.')

class ModuleForm(FlaskForm):
    title = StringField('Module Title', validators=[DataRequired()])
    description = TextAreaField('Module Description')
    submit = SubmitField('Create Module')

class LessonForm(FlaskForm):
    title = StringField('Lesson Title', validators=[DataRequired()])
    content = TextAreaField('Content')
    lesson_type = SelectField('Lesson Type', choices=[
        ('TEXT', 'Text'),
        ('VIDEO', 'Video'),
        ('PDF', 'PDF'),
        ('QUIZ', 'Quiz'),
        ('CODE', 'Code')
    ])
    file = FileField('Upload File', validators=[FileAllowed(['pdf', 'mp4', 'webm'])])
    submit = SubmitField('Create Lesson')

class AssignmentForm(FlaskForm):
    title = StringField('Assignment Title', validators=[DataRequired()])
    description = TextAreaField('Assignment Description', validators=[DataRequired()])
    due_date = DateTimeField('Due Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    points = IntegerField('Points', default=100)
    submit = SubmitField('Create Assignment')

class SubmissionForm(FlaskForm):
    content = TextAreaField('Submission Content')
    file = FileField('Upload File', validators=[FileAllowed(['pdf', 'doc', 'docx', 'zip', 'jpg', 'png', 'jpeg'])])
    submit = SubmitField('Submit Assignment')

class GradeSubmissionForm(FlaskForm):
    grade = IntegerField('Grade', validators=[DataRequired()])
    feedback = TextAreaField('Feedback')
    submit = SubmitField('Submit Grade')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[
        ('STUDENT', 'Student'),
        ('TEACHER', 'Teacher'),
        ('ADMIN', 'Admin')
    ])
    password = PasswordField('Password', validators=[Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    is_active = BooleanField('Active')
    submit = SubmitField('Save User')

    def __init__(self, user_id=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and (not self.user_id or user.id != self.user_id):
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and (not self.user_id or user.id != self.user_id):
            raise ValidationError('That email is already registered. Please use a different one.') 