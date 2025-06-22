from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
import enum
from werkzeug.security import generate_password_hash, check_password_hash

# Import db from app
from app import db

# User role enum
class UserRole(enum.Enum):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ADMIN = 'admin'

# User-Course association table (for enrollments)
enrollments = db.Table('enrollments',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    db.Column('enrollment_date', db.DateTime, default=datetime.utcnow),
    db.Column('status', db.String(20), default='active')  # active, completed, dropped
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    profile_image = db.Column(db.String(120), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Two-factor authentication
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)
    
    # Relationships
    courses_enrolled = db.relationship('Course', secondary=enrollments, 
                                      backref=db.backref('students', lazy='dynamic'))
    courses_teaching = db.relationship('Course', backref='teacher', lazy=True)
    submissions = db.relationship('Submission', backref='student', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    enrollments = db.relationship('Enrollment', back_populates='student', cascade='all, delete-orphan')
    chat_sessions = db.relationship('ChatSession', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)
    
    # Relationships
    teacher = db.relationship('User', back_populates='courses_teaching')
    modules = db.relationship('Module', back_populates='course', cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', back_populates='course', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', back_populates='course', cascade='all, delete-orphan')
    ratings = db.relationship('CourseRating', back_populates='course', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.title}>'

class Module(db.Model):
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Relationships
    course = db.relationship('Course', back_populates='modules')
    lessons = db.relationship('Lesson', back_populates='module', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Module {self.title}>'

class LessonType(enum.Enum):
    TEXT = 'text'
    VIDEO = 'video'
    PRESENTATION = 'presentation'
    INTERACTIVE = 'interactive'
    QUIZ = 'quiz'

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=True)
    type = db.Column(db.Enum(LessonType), nullable=False, default=LessonType.TEXT)
    order = db.Column(db.Integer, nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    video_url = db.Column(db.String(255), nullable=True)
    file_url = db.Column(db.String(255), nullable=True)
    
    # Relationships
    module = db.relationship('Module', back_populates='lessons')
    completions = db.relationship('LessonCompletion', back_populates='lesson', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Lesson {self.title}>'

class LessonCompletion(db.Model):
    __tablename__ = 'lesson_completions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User')
    lesson = db.relationship('Lesson', back_populates='completions')
    
    __table_args__ = (db.UniqueConstraint('student_id', 'lesson_id', name='uq_student_lesson'),)
    
    def __repr__(self):
        return f'<LessonCompletion student_id={self.student_id} lesson_id={self.lesson_id}>'

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    student = db.relationship('User', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')
    
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='uq_student_course'),)
    
    def __repr__(self):
        return f'<Enrollment student_id={self.student_id} course_id={self.course_id}>'

class AssignmentType(enum.Enum):
    TEXT = 'TEXT'
    FILE_UPLOAD = 'FILE_UPLOAD'
    CODE = 'CODE'
    QUIZ = 'QUIZ'
    PROJECT = 'PROJECT'

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.Enum(AssignmentType), nullable=False, default=AssignmentType.TEXT)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    points = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', back_populates='assignments')
    submissions = db.relationship('Submission', back_populates='assignment', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Assignment {self.title}>'

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(255), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    student = db.relationship('User', back_populates='submissions')
    assignment = db.relationship('Assignment', back_populates='submissions')
    
    __table_args__ = (db.UniqueConstraint('student_id', 'assignment_id', name='uq_student_assignment'),)
    
    def __repr__(self):
        return f'<Submission student_id={self.student_id} assignment_id={self.assignment_id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notification_type = db.Column(db.String(50), nullable=False)  # assignment, grade, announcement, etc.
    
    def __repr__(self):
        return f'<Notification {self.id} for user {self.user_id}>'

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False, default="New Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='chat_sessions')
    messages = db.relationship('ChatMessage', back_populates='session', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChatSession id={self.id} user_id={self.user_id}>'

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True if from user, False if from AI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    session = db.relationship('ChatSession', back_populates='messages')
    
    def __repr__(self):
        return f'<ChatMessage id={self.id} session_id={self.session_id} is_user={self.is_user}>'

class CourseRating(db.Model):
    __tablename__ = 'course_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User')
    course = db.relationship('Course', back_populates='ratings')
    
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='uq_student_course_rating'),)
    
    def __repr__(self):
        return f'<CourseRating student_id={self.student_id} course_id={self.course_id} rating={self.rating}>'

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<SystemSetting {self.key}>' 