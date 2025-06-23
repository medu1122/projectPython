from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('layout.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

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