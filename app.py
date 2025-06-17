from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, init_db
from models import User, Complaint
from ml_classifier.complaint_classifier import ComplaintClassifier
from chatbot import process_chatbot_message
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///complaints.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)
classifier = ComplaintClassifier()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id')
            name = request.form.get('name')
            designation = request.form.get('designation')
            phone = request.form.get('phone')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role', 'employee')  # Default to 'employee'

            # Validate required fields
            if not all([employee_id, name, designation, phone, email, password]):
                flash('All fields are required!')
                return redirect(url_for('register'))

            # Check for existing employee_id or email
            if User.query.filter_by(employee_id=employee_id).first():
                flash('Employee ID already exists!')
                return redirect(url_for('register'))
            if User.query.filter_by(email=email).first():
                flash('Email already registered!')
                return redirect(url_for('register'))

            # Create new user
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(
                employee_id=employee_id,
                name=name,
                designation=designation,
                phone=phone,
                email=email,
                password=hashed_password,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! Please login.')
            return redirect(url_for('login'))

        except KeyError as e:
            flash(f'Missing field: {e.args[0]}')
            return redirect(url_for('register'))
        except Exception as e:
            flash(f'Error: {str(e)}')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')  # Changed from 'email'
        password = request.form.get('password')
        if not all([employee_id, password]):
            flash('Employee ID and password are required!')
            return redirect(url_for('login'))

        user = User.query.filter_by(employee_id=employee_id).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'officer':
                return redirect(url_for('officer_dashboard'))
            elif user.role == 'it':
                return redirect(url_for('it_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    complaints = Complaint.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, complaints=complaints)

@app.route('/submit_complaint', methods=['GET', 'POST'])
def submit_complaint():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        complaint_type = request.form.get('complaint_type')
        department = request.form.get('department')
        description = request.form.get('description')
        if not all([complaint_type, department, description]):
            flash('All fields are required!')
            return redirect(url_for('submit_complaint'))
        
        category = classifier.predict(description)
        complaint = Complaint(
            user_id=session['user_id'],
            complaint_type=complaint_type,
            department=department,
            description=description,
            category=category,
            status='pending'
        )
        db.session.add(complaint)
        db.session.commit()
        flash(f'Complaint submitted successfully. Predicted category: {category}')
        return redirect(url_for('dashboard'))
    return render_template('submit_complaint.html')

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user_message = request.form.get('message')
        response = process_chatbot_message(user_message, session['user_id'])
        return jsonify({'response': response})
    return render_template('chatbot.html', user=user)

@app.route('/officer_dashboard')
def officer_dashboard():
    if 'user_id' not in session or session['role'] != 'officer':
        return redirect(url_for('login'))
    complaints = Complaint.query.filter_by(status='pending').all()
    return render_template('officer_dashboard.html', complaints=complaints)

@app.route('/approve_complaint/<int:complaint_id>')
def approve_complaint(complaint_id):
    if 'user_id' not in session or session['role'] != 'officer':
        return redirect(url_for('login'))
    complaint = Complaint.query.get(complaint_id)
    complaint.status = 'approved'
    db.session.commit()
    flash('Complaint approved!')
    return redirect(url_for('officer_dashboard'))

@app.route('/reject_complaint/<int:complaint_id>')
def reject_complaint(complaint_id):
    if 'user_id' not in session or session['role'] != 'officer':
        return redirect(url_for('login'))
    complaint = Complaint.query.get(complaint_id)
    complaint.status = 'rejected'
    db.session.commit()
    flash('Complaint rejected!')
    return redirect(url_for('officer_dashboard'))

@app.route('/it_dashboard')
def it_dashboard():
    if 'user_id' not in session or session['role'] != 'it':
        return redirect(url_for('login'))
    complaints = Complaint.query.filter_by(status='approved', department='IT').all()
    return render_template('it_dashboard.html', complaints=complaints)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
