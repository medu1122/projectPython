from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, bcrypt
from models import User, Course, Lesson, Enrollment, Assignment, Submission, ChatMessage, Rating
import os
import json
from datetime import datetime
import subprocess
import tempfile

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        user_exists = User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first()
        if user_exists:
            flash('Email or username already exists', 'danger')
            return render_template('register.html')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password, role='student')
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboard routes
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'student':
        enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
        upcoming_assignments = []
        
        for enrollment in enrollments:
            course_assignments = Assignment.query.filter_by(course_id=enrollment.course_id).all()
            for assignment in course_assignments:
                submission = Submission.query.filter_by(
                    student_id=current_user.id, 
                    assignment_id=assignment.id
                ).first()
                
                if not submission:
                    upcoming_assignments.append({
                        'title': assignment.title,
                        'course': enrollment.course.title,
                        'due_date': assignment.due_date,
                        'id': assignment.id
                    })
        
        return render_template('student/dashboard.html', 
                              enrollments=enrollments, 
                              upcoming_assignments=upcoming_assignments)
    
    elif current_user.role == 'teacher':
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
        stats = {
            'total_courses': len(courses),
            'total_students': sum(len(course.enrollments) for course in courses),
            'total_assignments': sum(len(course.assignments) for course in courses),
            'recent_submissions': Submission.query.join(Assignment).filter(
                Assignment.course_id.in_([course.id for course in courses])
            ).order_by(Submission.submitted_at.desc()).limit(5).all()
        }
        
        return render_template('teacher/dashboard.html', courses=courses, stats=stats)
    
    elif current_user.role == 'admin':
        stats = {
            'total_users': User.query.count(),
            'total_courses': Course.query.count(),
            'total_lessons': Lesson.query.count(),
            'total_assignments': Assignment.query.count()
        }
        
        return render_template('admin/dashboard.html', stats=stats)

# Course routes
@app.route('/courses')
@login_required
def courses():
    if current_user.role == 'student':
        enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
        available_courses = Course.query.filter(~Course.id.in_([e.course_id for e in enrollments])).all()
        return render_template('student/courses.html', enrollments=enrollments, available_courses=available_courses)
    
    elif current_user.role == 'teacher':
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
        return render_template('teacher/courses.html', courses=courses)
    
    elif current_user.role == 'admin':
        courses = Course.query.all()
        return render_template('admin/courses.html', courses=courses)

@app.route('/courses/<int:course_id>')
@login_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, 
            course_id=course_id
        ).first_or_404()
        
        lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order).all()
        assignments = Assignment.query.filter_by(course_id=course_id).all()
        
        # Get submission status for each assignment
        for assignment in assignments:
            submission = Submission.query.filter_by(
                student_id=current_user.id, 
                assignment_id=assignment.id
            ).first()
            
            assignment.submission_status = 'Submitted' if submission else 'Not Submitted'
            assignment.score = submission.score if submission else None
        
        return render_template('student/view_course.html', 
                              course=course, 
                              lessons=lessons, 
                              assignments=assignments,
                              enrollment=enrollment)
    
    elif current_user.role == 'teacher' and course.teacher_id == current_user.id:
        lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order).all()
        assignments = Assignment.query.filter_by(course_id=course_id).all()
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()
        
        return render_template('teacher/view_course.html', 
                              course=course, 
                              lessons=lessons, 
                              assignments=assignments,
                              enrollments=enrollments)
    
    elif current_user.role == 'admin':
        lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order).all()
        assignments = Assignment.query.filter_by(course_id=course_id).all()
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()
        
        return render_template('admin/view_course.html', 
                              course=course, 
                              lessons=lessons, 
                              assignments=assignments,
                              enrollments=enrollments)
    
    else:
        abort(403)

@app.route('/courses/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    if current_user.role != 'student':
        abort(403)
    
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id, 
        course_id=course_id
    ).first()
    
    if enrollment:
        flash('You are already enrolled in this course', 'info')
    else:
        enrollment = Enrollment(student_id=current_user.id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        flash('Successfully enrolled in the course', 'success')
    
    return redirect(url_for('view_course', course_id=course_id))

# Lesson routes
@app.route('/lessons/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    
    # Check if user has access to this lesson
    if current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, 
            course_id=course.id
        ).first()
        
        if not enrollment:
            abort(403)
    
    elif current_user.role == 'teacher' and course.teacher_id != current_user.id:
        abort(403)
    
    # Get all lessons for navigation
    all_lessons = Lesson.query.filter_by(course_id=course.id).order_by(Lesson.order).all()
    
    # Find previous and next lessons
    prev_lesson = None
    next_lesson = None
    
    for i, l in enumerate(all_lessons):
        if l.id == lesson_id:
            if i > 0:
                prev_lesson = all_lessons[i-1]
            if i < len(all_lessons) - 1:
                next_lesson = all_lessons[i+1]
            break
    
    return render_template('view_lesson.html', 
                          lesson=lesson, 
                          course=course, 
                          all_lessons=all_lessons,
                          prev_lesson=prev_lesson,
                          next_lesson=next_lesson)

# Assignment routes
@app.route('/assignments/<int:assignment_id>')
@login_required
def view_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    course = assignment.course
    
    # Check if user has access to this assignment
    if current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, 
            course_id=course.id
        ).first()
        
        if not enrollment:
            abort(403)
        
        submission = Submission.query.filter_by(
            student_id=current_user.id, 
            assignment_id=assignment_id
        ).first()
        
        return render_template('student/view_assignment.html', 
                              assignment=assignment, 
                              course=course,
                              submission=submission)
    
    elif current_user.role == 'teacher' and course.teacher_id == current_user.id:
        submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
        
        return render_template('teacher/view_assignment.html', 
                              assignment=assignment, 
                              course=course,
                              submissions=submissions)
    
    elif current_user.role == 'admin':
        submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
        
        return render_template('admin/view_assignment.html', 
                              assignment=assignment, 
                              course=course,
                              submissions=submissions)
    
    else:
        abort(403)

@app.route('/assignments/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    if current_user.role != 'student':
        abort(403)
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if user is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id, 
        course_id=assignment.course_id
    ).first()
    
    if not enrollment:
        abort(403)
    
    # Check if already submitted
    submission = Submission.query.filter_by(
        student_id=current_user.id, 
        assignment_id=assignment_id
    ).first()
    
    if submission:
        # Update existing submission
        if assignment.assignment_type == 'code':
            submission.content = request.form.get('code')
        elif assignment.assignment_type == 'quiz':
            submission.content = json.dumps(request.form)
        elif assignment.assignment_type == 'upload':
            if 'file' in request.files:
                file = request.files['file']
                if file.filename:
                    # Save uploaded file
                    filename = f"{current_user.id}_{assignment_id}_{file.filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    submission.file_path = file_path
    else:
        # Create new submission
        if assignment.assignment_type == 'code':
            submission = Submission(
                student_id=current_user.id,
                assignment_id=assignment_id,
                content=request.form.get('code')
            )
        elif assignment.assignment_type == 'quiz':
            submission = Submission(
                student_id=current_user.id,
                assignment_id=assignment_id,
                content=json.dumps(request.form)
            )
        elif assignment.assignment_type == 'upload':
            if 'file' in request.files:
                file = request.files['file']
                if file.filename:
                    # Save uploaded file
                    filename = f"{current_user.id}_{assignment_id}_{file.filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    submission = Submission(
                        student_id=current_user.id,
                        assignment_id=assignment_id,
                        file_path=file_path
                    )
    
    db.session.add(submission)
    db.session.commit()
    
    flash('Assignment submitted successfully', 'success')
    return redirect(url_for('view_assignment', assignment_id=assignment_id))

@app.route('/assignments/<int:assignment_id>/run_code', methods=['POST'])
@login_required
def run_code(assignment_id):
    if current_user.role != 'student':
        abort(403)
    
    assignment = Assignment.query.get_or_404(assignment_id)
    code = request.form.get('code')
    language = assignment.language
    
    if language == 'python':
        # Create a temporary file and run the code
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            temp_name = temp.name
            temp.write(code.encode('utf-8'))
        
        try:
            result = subprocess.run(['python', temp_name], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=5)
            
            output = result.stdout
            error = result.stderr
            
            os.unlink(temp_name)
            
            if error:
                return jsonify({'success': False, 'output': error})
            else:
                return jsonify({'success': True, 'output': output})
        
        except subprocess.TimeoutExpired:
            os.unlink(temp_name)
            return jsonify({'success': False, 'output': 'Execution timed out'})
        
        except Exception as e:
            os.unlink(temp_name)
            return jsonify({'success': False, 'output': str(e)})
    
    elif language == 'perl':
        # Similar implementation for Perl
        with tempfile.NamedTemporaryFile(suffix='.pl', delete=False) as temp:
            temp_name = temp.name
            temp.write(code.encode('utf-8'))
        
        try:
            result = subprocess.run(['perl', temp_name], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=5)
            
            output = result.stdout
            error = result.stderr
            
            os.unlink(temp_name)
            
            if error:
                return jsonify({'success': False, 'output': error})
            else:
                return jsonify({'success': True, 'output': output})
        
        except subprocess.TimeoutExpired:
            os.unlink(temp_name)
            return jsonify({'success': False, 'output': 'Execution timed out'})
        
        except Exception as e:
            os.unlink(temp_name)
            return jsonify({'success': False, 'output': str(e)})
    
    else:
        return jsonify({'success': False, 'output': f'Language {language} not supported'})

# Chatbot routes
@app.route('/chatbot')
@login_required
def chatbot():
    chat_history = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at).all()
    return render_template('chatbot.html', chat_history=chat_history)

@app.route('/chatbot/send', methods=['POST'])
@login_required
def send_message():
    message = request.form.get('message')
    
    # Save user message
    user_msg = ChatMessage(user_id=current_user.id, message=message, is_bot=False)
    db.session.add(user_msg)
    
    # Generate bot response (placeholder for AI integration)
    bot_response = "This is a placeholder response. AI integration will be implemented later."
    bot_msg = ChatMessage(user_id=current_user.id, message=bot_response, is_bot=True)
    db.session.add(bot_msg)
    
    db.session.commit()
    
    return jsonify({
        'user_message': message,
        'bot_response': bot_response
    })

# Rating routes
@app.route('/rate/<string:item_type>/<int:item_id>', methods=['POST'])
@login_required
def rate_item(item_type, item_id):
    if current_user.role != 'student':
        abort(403)
    
    stars = int(request.form.get('stars', 0))
    comment = request.form.get('comment', '')
    
    if stars < 1 or stars > 5:
        flash('Invalid rating', 'danger')
        return redirect(request.referrer)
    
    if item_type == 'course':
        course = Course.query.get_or_404(item_id)
        
        # Check if user is enrolled
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, 
            course_id=course.id
        ).first()
        
        if not enrollment:
            abort(403)
        
        # Check if already rated
        existing_rating = Rating.query.filter_by(
            student_id=current_user.id,
            course_id=course.id,
            lesson_id=None
        ).first()
        
        if existing_rating:
            existing_rating.stars = stars
            existing_rating.comment = comment
        else:
            rating = Rating(
                student_id=current_user.id,
                course_id=course.id,
                stars=stars,
                comment=comment
            )
            db.session.add(rating)
        
        db.session.commit()
        flash('Thank you for your rating!', 'success')
        return redirect(url_for('view_course', course_id=course.id))
    
    elif item_type == 'lesson':
        lesson = Lesson.query.get_or_404(item_id)
        
        # Check if user is enrolled in the course
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, 
            course_id=lesson.course_id
        ).first()
        
        if not enrollment:
            abort(403)
        
        # Check if already rated
        existing_rating = Rating.query.filter_by(
            student_id=current_user.id,
            course_id=lesson.course_id,
            lesson_id=lesson.id
        ).first()
        
        if existing_rating:
            existing_rating.stars = stars
            existing_rating.comment = comment
        else:
            rating = Rating(
                student_id=current_user.id,
                course_id=lesson.course_id,
                lesson_id=lesson.id,
                stars=stars,
                comment=comment
            )
            db.session.add(rating)
        
        db.session.commit()
        flash('Thank you for your rating!', 'success')
        return redirect(url_for('view_lesson', lesson_id=lesson.id))
    
    else:
        abort(404)

# Admin routes
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        abort(403)
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if current_user.role != 'admin':
        abort(403)
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        
        if request.form.get('password'):
            user.password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/courses/new', methods=['GET', 'POST'])
@login_required
def admin_new_course():
    if current_user.role != 'admin':
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        teacher_id = request.form.get('teacher_id')
        
        course = Course(
            title=title,
            description=description,
            teacher_id=teacher_id
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully', 'success')
        return redirect(url_for('courses'))
    
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('admin/new_course.html', teachers=teachers)

# Teacher routes
@app.route('/teacher/courses/new', methods=['GET', 'POST'])
@login_required
def teacher_new_course():
    if current_user.role != 'teacher':
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        course = Course(
            title=title,
            description=description,
            teacher_id=current_user.id
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully', 'success')
        return redirect(url_for('courses'))
    
    return render_template('teacher/new_course.html')

@app.route('/teacher/courses/<int:course_id>/lessons/new', methods=['GET', 'POST'])
@login_required
def teacher_new_lesson(course_id):
    if current_user.role != 'teacher':
        abort(403)
    
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        content_type = request.form.get('content_type')
        
        # Get the highest order value and add 1
        max_order = db.session.query(db.func.max(Lesson.order)).filter_by(course_id=course_id).scalar() or 0
        
        lesson = Lesson(
            title=title,
            content=content,
            content_type=content_type,
            course_id=course_id,
            order=max_order + 1
        )
        
        # Handle file upload if content_type is pdf or video
        if content_type in ['pdf', 'video'] and 'file' in request.files:
            file = request.files['file']
            if file.filename:
                # Save uploaded file
                filename = f"lesson_{course_id}_{file.filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                lesson.file_path = file_path
        
        db.session.add(lesson)
        db.session.commit()
        
        flash('Lesson created successfully', 'success')
        return redirect(url_for('view_course', course_id=course_id))
    
    return render_template('teacher/new_lesson.html', course=course)

@app.route('/teacher/courses/<int:course_id>/assignments/new', methods=['GET', 'POST'])
@login_required
def teacher_new_assignment(course_id):
    if current_user.role != 'teacher':
        abort(403)
    
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        assignment_type = request.form.get('assignment_type')
        due_date_str = request.form.get('due_date')
        
        due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M') if due_date_str else None
        
        assignment = Assignment(
            title=title,
            description=description,
            assignment_type=assignment_type,
            course_id=course_id,
            due_date=due_date
        )
        
        if assignment_type == 'code':
            assignment.language = request.form.get('language')
            assignment.test_cases = request.form.get('test_cases')
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Assignment created successfully', 'success')
        return redirect(url_for('view_course', course_id=course_id))
    
    return render_template('teacher/new_assignment.html', course=course)

@app.route('/teacher/submissions/<int:submission_id>/grade', methods=['POST'])
@login_required
def grade_submission(submission_id):
    if current_user.role != 'teacher':
        abort(403)
    
    submission = Submission.query.get_or_404(submission_id)
    assignment = submission.assignment
    
    if assignment.course.teacher_id != current_user.id:
        abort(403)
    
    score = float(request.form.get('score', 0))
    feedback = request.form.get('feedback', '')
    
    submission.score = score
    submission.feedback = feedback
    
    db.session.commit()
    
    flash('Submission graded successfully', 'success')
    return redirect(url_for('view_assignment', assignment_id=assignment.id)) 