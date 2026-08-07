from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import csv
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
bcrypt = Bcrypt(app)

# Cloud PostgreSQL Database Connection using your teammate's credentials
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Capstone2026@capstone-db.c58cco4wmxkt.eu-north-1.rds.amazonaws.com:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Predefined courses list
PREDEFINED_COURSES = ["Automata Theory", "Database Systems", "Software Engineering", "Computer Networks"]

# Temporary mock fallback until teammate finishes table schemas
fake_users_db = {}
attendance_records = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        if email in fake_users_db:
            return "Registration error: Email already exists! <a href='/register'>Try again</a>"
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        fake_users_db[email] = {
            'name': name,
            'email': email,
            'password_hash': hashed_password,
            'role': role
        }
        return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = fake_users_db.get(email)
        
        if user and bcrypt.check_password_hash(user['password_hash'], password):
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            session['user_email'] = user['email']
            
            if user['role'] == 'instructor':
                return redirect(url_for('instructor_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            return "Invalid email or password. <a href='/login'>Try again</a>"
            
    return render_template('login.html')

@app.route('/instructor', methods=['GET', 'POST'])
def instructor_dashboard():
    if 'user_role' in session and session['user_role'] == 'instructor':
        if request.method == 'POST':
            course = request.form['course']
            date = request.form['date']
            status = request.form['status']
            student_email = request.form['student_email']
            
            attendance_records.append({
                'course': course,
                'date': date,
                'student_email': student_email,
                'status': status
            })
            
        return render_template('instructor.html', name=session['user_name'], records=attendance_records, students=fake_users_db, courses=PREDEFINED_COURSES)
    return redirect(url_for('login'))

@app.route('/student')
def student_dashboard():
    if 'user_role' in session and session['user_role'] == 'student':
        student_email = session['user_email']
        my_records = [r for r in attendance_records if r['student_email'] == student_email]
        
        total_classes = len(my_records)
        present_count = len([r for r in my_records if r['status'] == 'Present'])
        percentage = round((present_count / total_classes * 100), 1) if total_classes > 0 else 0
        
        return render_template('student.html', name=session['user_name'], records=my_records, total=total_classes, present=present_count, percentage=percentage)
    return redirect(url_for('login'))

@app.route('/export_csv')
def export_csv():
    if 'user_role' in session and session['user_role'] == 'instructor':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Course', 'Date', 'Student Email', 'Status'])
        for rec in attendance_records:
            writer.writerow([rec['course'], rec['date'], rec['student_email'], rec['status']])
        output.seek(0)
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=attendance_report.csv"}
        )
    return redirect(url_for('login'))

@app.route('/delete/<int:index>', methods=['POST'])
def delete_attendance(index):
    if 'user_role' in session and session['user_role'] == 'instructor':
        if 0 <= index < len(attendance_records):
            attendance_records.pop(index)
    return redirect(url_for('instructor_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)