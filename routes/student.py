from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from models import Course, Module, Lesson, Assignment, Submission, LessonCompletion, ChatSession, ChatMessage, UserRole
from functools import wraps
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app

student_bp = Blueprint('student', __name__)

# Custom decorator to ensure user is a student
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.STUDENT:
            flash('Access denied. You must be a student to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    """Student dashboard route"""
    # Get enrolled courses
    enrolled_courses = current_user.courses_enrolled
    
    # Get upcoming assignments
    upcoming_assignments = []
    for course in enrolled_courses:
        assignments = Assignment.query.filter_by(course_id=course.id).filter(
            Assignment.due_date > datetime.utcnow()
        ).order_by(Assignment.due_date).limit(5).all()
        upcoming_assignments.extend(assignments)
    
    # Sort by due date
    upcoming_assignments.sort(key=lambda x: x.due_date)
    
    # Get recent submissions
    recent_submissions = Submission.query.filter_by(student_id=current_user.id).order_by(
        Submission.submitted_at.desc()
    ).limit(5).all()
    
    return render_template('student/dashboard.html', 
                          enrolled_courses=enrolled_courses,
                          upcoming_assignments=upcoming_assignments,
                          recent_submissions=recent_submissions)

@student_bp.route('/courses')
@login_required
@student_required
def courses():
    """Student's enrolled courses route"""
    enrolled_courses = current_user.courses_enrolled
    
    # Get available courses for enrollment
    available_courses = Course.query.filter_by(is_active=True).all()
    available_courses = [course for course in available_courses if course not in enrolled_courses]
    
    return render_template('student/courses.html', 
                          enrolled_courses=enrolled_courses,
                          available_courses=available_courses)

@student_bp.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
@student_required
def enroll(course_id):
    """Enroll in a course route"""
    course = Course.query.get_or_404(course_id)
    
    if course in current_user.courses_enrolled:
        flash('You are already enrolled in this course.', 'info')
    else:
        current_user.courses_enrolled.append(course)
        db.session.commit()
        flash(f'You have successfully enrolled in {course.title}.', 'success')
    
    return redirect(url_for('student.courses'))

@student_bp.route('/course/<int:course_id>')
@login_required
@student_required
def view_course(course_id):
    """View course content route"""
    course = Course.query.get_or_404(course_id)
    
    # Check if student is enrolled
    if course not in current_user.courses_enrolled:
        flash('You must be enrolled in this course to view its content.', 'danger')
        return redirect(url_for('student.courses'))
    
    # Get completed lessons
    completed_lessons = [completion.lesson_id for completion in current_user.completed_lessons]
    
    # Calculate progress
    total_lessons = sum(len(module.lessons) for module in course.modules)
    completed_count = sum(1 for module in course.modules for lesson in module.lessons if lesson.id in completed_lessons)
    
    progress = 0
    if total_lessons > 0:
        progress = (completed_count / total_lessons) * 100
    
    return render_template('student/view_course.html', 
                          course=course, 
                          completed_lessons=completed_lessons,
                          progress=progress)

@student_bp.route('/lesson/<int:lesson_id>')
@login_required
@student_required
def view_lesson(lesson_id):
    """View lesson content route"""
    lesson = Lesson.query.get_or_404(lesson_id)
    module = lesson.module
    course = module.course
    
    # Check if student is enrolled
    if course not in current_user.courses_enrolled:
        flash('You must be enrolled in this course to view its lessons.', 'danger')
        return redirect(url_for('student.courses'))
    
    # Get next and previous lessons for navigation
    lessons_in_module = module.lessons
    current_index = next((i for i, l in enumerate(lessons_in_module) if l.id == lesson.id), None)
    
    prev_lesson = lessons_in_module[current_index - 1] if current_index > 0 else None
    next_lesson = lessons_in_module[current_index + 1] if current_index < len(lessons_in_module) - 1 else None
    
    # Check if lesson is already completed
    is_completed = LessonCompletion.query.filter_by(
        user_id=current_user.id, 
        lesson_id=lesson.id
    ).first() is not None
    
    return render_template('student/view_lesson.html', 
                          lesson=lesson,
                          module=module,
                          course=course,
                          prev_lesson=prev_lesson,
                          next_lesson=next_lesson,
                          is_completed=is_completed)

@student_bp.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
@student_required
def complete_lesson(lesson_id):
    """Mark lesson as completed route"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check if already completed
    existing = LessonCompletion.query.filter_by(
        user_id=current_user.id, 
        lesson_id=lesson.id
    ).first()
    
    if not existing:
        completion = LessonCompletion(user_id=current_user.id, lesson_id=lesson.id)
        db.session.add(completion)
        db.session.commit()
    
    # Redirect to next lesson if available
    module = lesson.module
    lessons_in_module = module.lessons
    current_index = next((i for i, l in enumerate(lessons_in_module) if l.id == lesson.id), None)
    
    if current_index < len(lessons_in_module) - 1:
        next_lesson = lessons_in_module[current_index + 1]
        return redirect(url_for('student.view_lesson', lesson_id=next_lesson.id))
    else:
        # If last lesson in module, go back to course page
        return redirect(url_for('student.view_course', course_id=module.course.id))

@student_bp.route('/assignments')
@login_required
@student_required
def assignments():
    """View all assignments route"""
    # Get assignments from enrolled courses
    course_ids = [course.id for course in current_user.courses_enrolled]
    
    # Filter assignments by these courses
    assignments = Assignment.query.filter(Assignment.course_id.in_(course_ids)).order_by(
        Assignment.due_date
    ).all()
    
    # Group by status: upcoming, submitted, graded
    upcoming = []
    submitted = []
    graded = []
    
    for assignment in assignments:
        submission = Submission.query.filter_by(
            assignment_id=assignment.id,
            student_id=current_user.id
        ).first()
        
        if submission:
            if submission.grade is not None:
                graded.append((assignment, submission))
            else:
                submitted.append((assignment, submission))
        else:
            upcoming.append((assignment, None))
    
    return render_template('student/assignments.html',
                          upcoming=upcoming,
                          submitted=submitted,
                          graded=graded)

@student_bp.route('/assignment/<int:assignment_id>')
@login_required
@student_required
def view_assignment(assignment_id):
    """View assignment details route"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if student is enrolled in the course
    if assignment.course not in current_user.courses_enrolled:
        flash('You must be enrolled in this course to view its assignments.', 'danger')
        return redirect(url_for('student.assignments'))
    
    # Get submission if exists
    submission = Submission.query.filter_by(
        assignment_id=assignment.id,
        student_id=current_user.id
    ).first()
    
    return render_template('student/view_assignment.html',
                          assignment=assignment,
                          submission=submission)

@student_bp.route('/assignment/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
@student_required
def submit_assignment(assignment_id):
    """Submit assignment route"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if student is enrolled in the course
    if assignment.course not in current_user.courses_enrolled:
        flash('You must be enrolled in this course to submit assignments.', 'danger')
        return redirect(url_for('student.assignments'))
    
    # Check if already submitted
    existing_submission = Submission.query.filter_by(
        assignment_id=assignment.id,
        student_id=current_user.id
    ).first()
    
    if request.method == 'POST':
        content = request.form.get('content')
        file = request.files.get('file')
        
        if existing_submission:
            # Update existing submission
            existing_submission.content = content
            
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'submissions', filename)
                file.save(file_path)
                existing_submission.file_path = filename
            
            existing_submission.submitted_at = datetime.utcnow()
            db.session.commit()
            flash('Your submission has been updated.', 'success')
        else:
            # Create new submission
            file_path = None
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'submissions', filename)
                file.save(file_path)
            
            submission = Submission(
                assignment_id=assignment.id,
                student_id=current_user.id,
                content=content,
                file_path=filename if file and file.filename else None
            )
            
            db.session.add(submission)
            db.session.commit()
            flash('Your assignment has been submitted successfully.', 'success')
        
        return redirect(url_for('student.view_assignment', assignment_id=assignment.id))
    
    return render_template('student/submit_assignment.html',
                          assignment=assignment,
                          submission=existing_submission)

@student_bp.route('/chatbot')
@login_required
@student_required
def chatbot():
    """AI chatbot assistant route"""
    # Get or create active chat session
    active_session = ChatSession.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatSession.created_at.desc()).first()
    
    if not active_session:
        active_session = ChatSession(
            user_id=current_user.id,
            title='New Chat'
        )
        db.session.add(active_session)
        db.session.commit()
    
    # Get all user's chat sessions
    all_sessions = ChatSession.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatSession.created_at.desc()).all()
    
    return render_template('chatbot.html',
                          active_session=active_session,
                          all_sessions=all_sessions)

@student_bp.route('/chatbot/send', methods=['POST'])
@login_required
@student_required
def send_message():
    """Send message to chatbot route"""
    session_id = request.form.get('session_id')
    message_content = request.form.get('message')
    
    if not session_id or not message_content:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Get the chat session
    session = ChatSession.query.get_or_404(session_id)
    
    # Ensure the session belongs to the current user
    if session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Add user message to database
    user_message = ChatMessage(
        session_id=session_id,
        is_user=True,
        content=message_content
    )
    db.session.add(user_message)
    
    # Generate AI response (implementation would depend on your AI integration)
    ai_response = generate_ai_response(message_content)
    
    # Add AI response to database
    ai_message = ChatMessage(
        session_id=session_id,
        is_user=False,
        content=ai_response
    )
    db.session.add(ai_message)
    
    # Update session title for new sessions
    if session.title == 'New Chat' and len(message_content) > 0:
        session.title = message_content[:30] + ('...' if len(message_content) > 30 else '')
    
    db.session.commit()
    
    return jsonify({
        'user_message': {
            'content': user_message.content,
            'timestamp': user_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        },
        'ai_message': {
            'content': ai_message.content,
            'timestamp': ai_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@student_bp.route('/chatbot/new-session', methods=['POST'])
@login_required
@student_required
def new_chat_session():
    """Create new chat session route"""
    new_session = ChatSession(
        user_id=current_user.id,
        title='New Chat'
    )
    db.session.add(new_session)
    db.session.commit()
    
    return redirect(url_for('student.chatbot'))

# Helper function for AI response generation
def generate_ai_response(message):
    """Generate AI response using OpenAI API"""
    try:
        import openai
        from flask import current_app
        
        openai.api_key = current_app.config['OPENAI_API_KEY']
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful learning assistant for an online education platform."},
                {"role": "user", "content": message}
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        # Fallback response if API call fails
        return f"I'm sorry, I couldn't process your request at the moment. Please try again later. (Error: {str(e)})" 