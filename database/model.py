from database.config import db
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Chỉ định sử dụng table 'users'
    
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(255),nullable=False)
    email=db.Column(db.String(255),nullable=False,unique=True)
    password=db.Column(db.String(255),nullable=False)
    avatar=db.Column(db.String(255),nullable=True)
    role=db.Column(db.String(255),nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.now)
    is_active=db.Column(db.Boolean,default=True)
    
    # Relationships
    taught_courses = db.relationship('Course', backref='teacher', lazy=True, foreign_keys='Course.teacher_id')
    enrolled_courses = db.relationship('UserCourse', backref='student', lazy=True)
    lesson_progress = db.relationship('UserProgress', backref='user', lazy=True)
    
    def get_id(self):
        return str(self.id)
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def is_active_user(self):
        return self.is_active

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Relationships
    courses = db.relationship('Course', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    level = db.Column(db.String(50), nullable=True)  # beginner, intermediate, advanced
    thumbnail = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships  
    enrollments = db.relationship('UserCourse', backref='course', lazy=True)
    modules = db.relationship('Module', backref='course', lazy=True, order_by='Module.order_index')
    
    @property
    def name(self):
        return self.title
    
    @property
    def image(self):
        return self.thumbnail
    
    @property
    def student_count(self):
        return UserCourse.query.filter_by(course_id=self.id).count()
    
    @property
    def total_lessons(self):
        return sum(module.lesson_count for module in self.modules)
    
    @property
    def average_progress(self):
        enrollments = UserCourse.query.filter_by(course_id=self.id).all()
        if not enrollments:
            return 0
        return sum(e.progress for e in enrollments) / len(enrollments)
    
    def get_user_progress(self, user_id):
        """Calculate user's progress in this course"""
        total_lessons = self.total_lessons
        if total_lessons == 0:
            return 0
        
        completed_lessons = UserProgress.query.join(Lesson).join(Module).filter(
            Module.course_id == self.id,
            UserProgress.user_id == user_id,
            UserProgress.is_completed == True
        ).count()
        
        return (completed_lessons / total_lessons) * 100
    
    def __repr__(self):
        return f'<Course {self.title}>'

class UserCourse(db.Model):
    __tablename__ = 'user_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.now)
    progress = db.Column(db.Float, default=0.0)  # Progress percentage (0-100)
    
    @property
    def progress_percentage(self):
        return f"{self.progress:.1f}%"
    
    @property
    def is_completed(self):
        return self.progress >= 100.0
    
    def __repr__(self):
        return f'<UserCourse User:{self.user_id} Course:{self.course_id}>'

class Module(db.Model):
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    lessons = db.relationship('Lesson', backref='module', lazy=True, order_by='Lesson.order_index')
    
    @property
    def lesson_count(self):
        return len(self.lessons)
    
    def __repr__(self):
        return f'<Module {self.title}>'

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    lesson_type = db.Column(db.String(50), nullable=False)  # video, text, quiz, assignment, code
    duration_minutes = db.Column(db.Integer, nullable=True)  # Estimated completion time
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    contents = db.relationship('LessonContent', backref='lesson', lazy=True, order_by='LessonContent.order_index')
    user_progress = db.relationship('UserProgress', backref='lesson', lazy=True)
    
    @property
    def content_count(self):
        return len(self.contents)
    
    def is_completed_by_user(self, user_id):
        progress = UserProgress.query.filter_by(
            user_id=user_id,
            lesson_id=self.id
        ).first()
        return progress and progress.is_completed
    
    def __repr__(self):
        return f'<Lesson {self.title}>'

class LessonContent(db.Model):
    __tablename__ = 'lesson_contents'
    
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # text, video, file, quiz, code_exercise
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=True)  # Text content or JSON for complex content
    file_path = db.Column(db.String(500), nullable=True)  # Path to uploaded files
    order_index = db.Column(db.Integer, nullable=False, default=0)
    is_required = db.Column(db.Boolean, default=True)  # Must complete to progress
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<LessonContent {self.content_type}: {self.title}>'

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completion_percentage = db.Column(db.Float, default=0.0)  # For partial completion
    time_spent_minutes = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.now)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Unique constraint to prevent duplicate records
    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id', name='unique_user_lesson'),)
    
    def mark_completed(self):
        self.is_completed = True
        self.completion_percentage = 100.0
        self.completed_at = datetime.now()
    
    def __repr__(self):
        return f'<UserProgress User:{self.user_id} Lesson:{self.lesson_id} ({self.completion_percentage}%)>'