from flask import Flask, render_template
from database.config import db, app
from auth import auth
from database.heath import heath, init_db

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(heath)

# Khởi tạo cơ sở dữ liệu
init_db(app)

# Remove duplicate routes now handled by auth blueprint
@app.route('/')
def index():
    return render_template('layout.html')

@app.route('/student/dashboard')
def student_dashboard():
    return render_template('student/dashboard.html')

@app.route('/teacher/dashboard')
def teacher_dashboard():
    return render_template('teacher/dashboard.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

if __name__ == '__main__':
    app.run(debug=True) 