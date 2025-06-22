import os
from app import create_app, db
from models import User, UserRole, Course, Module, Lesson, LessonCompletion, Assignment, Submission, CourseRating, ChatSession, ChatMessage, SystemSetting

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    """Make variables available in Flask shell."""
    return {
        'db': db, 
        'User': User, 
        'UserRole': UserRole,
        'Course': Course, 
        'Module': Module, 
        'Lesson': Lesson,
        'LessonCompletion': LessonCompletion,
        'Assignment': Assignment, 
        'Submission': Submission,
        'CourseRating': CourseRating,
        'ChatSession': ChatSession,
        'ChatMessage': ChatMessage,
        'SystemSetting': SystemSetting
    }

if __name__ == '__main__':
    app.run(debug=True) 