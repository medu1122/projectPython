# Learning Management System (Frontend Only)

This is a frontend-only implementation of a Learning Management System built with Flask. It provides a UI demonstration of the system without any backend functionality.

## Features

- User interface for students, teachers, and administrators
- Course display and navigation
- Assignment viewing
- AI Chatbot interface
- Dark mode support
- Responsive design

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/flask-boilerplate.git
cd flask-boilerplate
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```
pip install -r requirements.txt
```

4. Run the application:
```
python run.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Demo Access

The application provides demonstration access to different user roles:

- **Student Dashboard**: http://localhost:5000/student/dashboard
- **Teacher Dashboard**: http://localhost:5000/teacher/dashboard
- **Admin Dashboard**: http://localhost:5000/admin/dashboard
- **AI Chatbot**: http://localhost:5000/chatbot

## Project Structure

```
flask-boilerplate/
├── app.py                  # Main application file
├── config.py               # Configuration settings
├── requirements.txt        # Project dependencies
├── run.py                  # Application entry point
├── static/                 # Static files (CSS, JS, images)
│   ├── css/                # CSS files
│   ├── js/                 # JavaScript files
│   └── img/                # Images and icons
└── templates/              # HTML templates
    ├── admin/              # Admin templates
    ├── student/            # Student templates
    ├── teacher/            # Teacher templates
    ├── errors/             # Error pages
    ├── layout.html         # Base template
    ├── login.html          # Login page
    ├── register.html       # Registration page
    └── chatbot.html        # AI Chatbot page
```

## Note

This is a frontend-only implementation meant for UI demonstration purposes. No actual backend functionality (database, authentication, etc.) is implemented. User interactions are simulated with JavaScript. 
- **User Management**
  - Role-based access control (Student, Teacher, Admin)
  - User authentication and authorization
  - Profile management

- **Course Management**
  - Course creation and organization
  - Module and lesson structure
  - Multiple content formats (text, video, presentations)
  - Progress tracking

- **Assignment System**
  - Assignment creation and submission
  - Grading and feedback
  - Due date management

- **AI Learning Assistant**
  - Intelligent chatbot for student support
  - Course-specific help
  - Learning recommendations

- **Analytics and Reporting**
  - Student progress tracking
  - Course completion rates
  - Performance metrics

## Technology Stack

- **Backend**: Python, Flask
- **Database**: SQLAlchemy ORM (supports SQLite, PostgreSQL, MS SQL Server)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Email**: Flask-Mail
- **AI Integration**: OpenAI API

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/learning-management-system.git
   cd learning-management-system
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (create a .env file):
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key
   DATABASE_URL=your-database-url
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-email-password
   OPENAI_API_KEY=your-openai-api-key
   ```

5. Initialize the database:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. Run the application:
   ```bash
   flask run
   ```

## Project Structure

```
learning-management-system/
├── app.py                  # Application factory
├── config.py               # Configuration settings
├── models.py               # Database models
├── forms.py                # Form classes
├── routes/                 # Route blueprints
│   ├── __init__.py
│   ├── main.py
│   ├── auth.py
│   ├── student.py
│   ├── teacher.py
│   ├── admin.py
│   └── api.py
├── static/                 # Static files
│   ├── css/
│   ├── js/
│   └── uploads/
├── templates/              # HTML templates
│   ├── layout.html
│   ├── errors/
│   ├── auth/
│   ├── student/
│   ├── teacher/
│   └── admin/
├── errors.py               # Error handlers
├── cli.py                  # Command-line commands
└── run.py                  # Application entry point
```

## Usage

### Admin
- Create and manage users, courses, and system settings
- View analytics and reports

### Teacher
- Create and manage courses, modules, and lessons
- Create assignments and grade submissions
- Track student progress

### Student
- Enroll in courses
- Access course materials and complete lessons
- Submit assignments
- Get help from the AI assistant

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Flask and its extensions
- OpenAI for the AI assistant functionality
- Bootstrap for the frontend framework 