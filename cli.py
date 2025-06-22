import click
from flask.cli import with_appcontext
from app import db, bcrypt
from models import User, UserRole, Course, Module, Lesson, LessonType
import os
import random
from datetime import datetime, timedelta

def register_commands(app):
    """Register CLI commands for the Flask application"""
    
    @app.cli.command('create-db')
    @with_appcontext
    def create_db():
        """Create database tables"""
        db.create_all()
        click.echo('Database tables created successfully.')
    
    @app.cli.command('drop-db')
    @with_appcontext
    def drop_db():
        """Drop all database tables"""
        if click.confirm('Are you sure you want to drop all database tables?'):
            db.drop_all()
            click.echo('Database tables dropped successfully.')
    
    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('email')
    @click.argument('password')
    @with_appcontext
    def create_admin(username, email, password):
        """Create admin user"""
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            click.echo(f'User {username} already exists.')
            return
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            click.echo(f'Email {email} already in use.')
            return
        
        # Create admin user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = User(
            username=username,
            email=email,
            password=hashed_password,
            first_name='Admin',
            last_name='User',
            role=UserRole.ADMIN
        )
        
        db.session.add(admin)
        db.session.commit()
        
        click.echo(f'Admin user {username} created successfully.')
    
    @app.cli.command('seed-db')
    @with_appcontext
    def seed_db():
        """Seed database with sample data"""
        if click.confirm('This will add sample data to the database. Continue?'):
            # Create users
            create_sample_users()
            
            # Create courses
            create_sample_courses()
            
            click.echo('Database seeded successfully.')
    
    @app.cli.command('reset-password')
    @click.argument('email')
    @click.argument('new_password')
    @with_appcontext
    def reset_password(email, new_password):
        """Reset user password by email"""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            click.echo(f'No user found with email {email}.')
            return
        
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        
        click.echo(f'Password reset successfully for {email}.')
    
    @app.cli.command('list-users')
    @with_appcontext
    def list_users():
        """List all users"""
        users = User.query.all()
        
        if not users:
            click.echo('No users found.')
            return
        
        click.echo('Users:')
        for user in users:
            click.echo(f'ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role.name}')
    
    @app.cli.command('list-courses')
    @with_appcontext
    def list_courses():
        """List all courses"""
        courses = Course.query.all()
        
        if not courses:
            click.echo('No courses found.')
            return
        
        click.echo('Courses:')
        for course in courses:
            teacher = User.query.get(course.teacher_id)
            teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher else "Unknown"
            click.echo(f'ID: {course.id}, Title: {course.title}, Code: {course.code}, Teacher: {teacher_name}')

def create_sample_users():
    """Create sample users for the database"""
    # Create teachers
    teachers = [
        {
            'username': 'teacher1',
            'email': 'teacher1@example.com',
            'password': 'password123',
            'first_name': 'John',
            'last_name': 'Smith'
        },
        {
            'username': 'teacher2',
            'email': 'teacher2@example.com',
            'password': 'password123',
            'first_name': 'Jane',
            'last_name': 'Doe'
        }
    ]
    
    teacher_ids = []
    
    for teacher_data in teachers:
        # Check if user already exists
        existing_user = User.query.filter_by(username=teacher_data['username']).first()
        if existing_user:
            teacher_ids.append(existing_user.id)
            continue
        
        # Create teacher
        hashed_password = bcrypt.generate_password_hash(teacher_data['password']).decode('utf-8')
        teacher = User(
            username=teacher_data['username'],
            email=teacher_data['email'],
            password=hashed_password,
            first_name=teacher_data['first_name'],
            last_name=teacher_data['last_name'],
            role=UserRole.TEACHER
        )
        
        db.session.add(teacher)
        db.session.commit()
        
        teacher_ids.append(teacher.id)
        click.echo(f"Created teacher: {teacher_data['username']}")
    
    # Create students
    students = [
        {
            'username': 'student1',
            'email': 'student1@example.com',
            'password': 'password123',
            'first_name': 'Alice',
            'last_name': 'Johnson'
        },
        {
            'username': 'student2',
            'email': 'student2@example.com',
            'password': 'password123',
            'first_name': 'Bob',
            'last_name': 'Williams'
        },
        {
            'username': 'student3',
            'email': 'student3@example.com',
            'password': 'password123',
            'first_name': 'Charlie',
            'last_name': 'Brown'
        }
    ]
    
    student_ids = []
    
    for student_data in students:
        # Check if user already exists
        existing_user = User.query.filter_by(username=student_data['username']).first()
        if existing_user:
            student_ids.append(existing_user.id)
            continue
        
        # Create student
        hashed_password = bcrypt.generate_password_hash(student_data['password']).decode('utf-8')
        student = User(
            username=student_data['username'],
            email=student_data['email'],
            password=hashed_password,
            first_name=student_data['first_name'],
            last_name=student_data['last_name'],
            role=UserRole.STUDENT
        )
        
        db.session.add(student)
        db.session.commit()
        
        student_ids.append(student.id)
        click.echo(f"Created student: {student_data['username']}")
    
    return teacher_ids, student_ids

def create_sample_courses():
    """Create sample courses for the database"""
    # Get teacher IDs
    teacher_ids, student_ids = create_sample_users()
    
    if not teacher_ids:
        click.echo('No teachers available to create courses.')
        return
    
    # Create courses
    courses = [
        {
            'title': 'Introduction to Python',
            'description': 'Learn the basics of Python programming language',
            'code': 'PY101',
            'teacher_id': teacher_ids[0]
        },
        {
            'title': 'Web Development with Flask',
            'description': 'Build web applications using Flask framework',
            'code': 'WD201',
            'teacher_id': teacher_ids[0]
        },
        {
            'title': 'Data Science Fundamentals',
            'description': 'Introduction to data analysis and visualization',
            'code': 'DS101',
            'teacher_id': teacher_ids[1] if len(teacher_ids) > 1 else teacher_ids[0]
        }
    ]
    
    course_ids = []
    
    for course_data in courses:
        # Check if course already exists
        existing_course = Course.query.filter_by(code=course_data['code']).first()
        if existing_course:
            course_ids.append(existing_course.id)
            continue
        
        # Create course
        course = Course(
            title=course_data['title'],
            description=course_data['description'],
            code=course_data['code'],
            teacher_id=course_data['teacher_id'],
            is_active=True,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=90)
        )
        
        db.session.add(course)
        db.session.commit()
        
        course_ids.append(course.id)
        click.echo(f"Created course: {course_data['title']}")
        
        # Create modules and lessons
        create_sample_modules(course.id)
        
        # Enroll students
        for student_id in student_ids:
            student = User.query.get(student_id)
            if student and course not in student.courses_enrolled:
                student.courses_enrolled.append(course)
        
        db.session.commit()
    
    return course_ids

def create_sample_modules(course_id):
    """Create sample modules and lessons for a course"""
    # Create modules
    modules = [
        {
            'title': 'Getting Started',
            'description': 'Introduction to the course',
            'order': 1
        },
        {
            'title': 'Basic Concepts',
            'description': 'Fundamental concepts and principles',
            'order': 2
        },
        {
            'title': 'Advanced Topics',
            'description': 'Advanced concepts and techniques',
            'order': 3
        }
    ]
    
    for module_data in modules:
        # Create module
        module = Module(
            title=module_data['title'],
            description=module_data['description'],
            course_id=course_id,
            order=module_data['order']
        )
        
        db.session.add(module)
        db.session.commit()
        
        # Create lessons
        create_sample_lessons(module.id)

def create_sample_lessons(module_id):
    """Create sample lessons for a module"""
    # Create lessons
    lessons = [
        {
            'title': 'Introduction',
            'content': 'Welcome to the lesson! This is the introduction.',
            'lesson_type': LessonType.TEXT,
            'order': 1
        },
        {
            'title': 'Key Concepts',
            'content': 'In this lesson, we will cover the key concepts.',
            'lesson_type': LessonType.TEXT,
            'order': 2
        },
        {
            'title': 'Practical Examples',
            'content': 'Let\'s look at some practical examples.',
            'lesson_type': LessonType.TEXT,
            'order': 3
        }
    ]
    
    for lesson_data in lessons:
        # Create lesson
        lesson = Lesson(
            title=lesson_data['title'],
            content=lesson_data['content'],
            module_id=module_id,
            lesson_type=lesson_data['lesson_type'],
            order=lesson_data['order']
        )
        
        db.session.add(lesson)
    
    db.session.commit()

if __name__ == '__main__':
    # This allows the file to be imported as a module
    pass 