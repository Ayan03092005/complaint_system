from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, init_db
from models import User, Complaint
from ml_classifier.complaint_classifier import ComplaintClassifier
from chatbot import process_chatbot_message
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = '3ba5cf9cf8a44fc11c725ade193d67ca5accd1a89ca0bf0e'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///complaints.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)
classifier = ComplaintClassifier()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            employee_id = request.form['employee_id']
            name = request.form['name']
            designation = request.form['designation']
            phone = request.form['phone']
            email = request.form['email']
            password = request.form['password']
            role = request.form['role', 'employee']  # Default to 'employee' if designation not in ['officer', 'it']
            
            if User.query.filter_by(employee_id=employee_id).first():
                flash('Employee ID already exists!')
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered!')
                return redirect(url_for('register'))
            
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(
                employee_id=employee_id,
                name=name,
                designation=designation,
                phone=phone,
                email=email,
                password=has_password,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
            
        except KeyError as e:
            flash(f'Missing field: {e.args[0]}')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    complaints = Complaint.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, complaints=complaints)

@app.route('/officer_dashboard')
def officer_dashboard():
    if 'user_id' not in session or session['role'] != 'officer':
        flash('Unauthorized access.')
        return redirect(url_for('login'))
    complaints = Complaint.query.all()
    return render_template('officer_dashboard.html', complaints=complaints)

@app.route('/it_dashboard')
def it_dashboard():
    if 'user_id' not in session or session['role'] != 'it':
        flash('Unauthorized access.')
        return redirect(url_for('login'))
    complaints = Complaint.query.filter_by(category='technical').all()
    return render_template('it_dashboard.html', complaints=complaints)

@app.route('/submit_complaint', methods=['GET', 'POST'])
def submit_complaint():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        complaint_type = request.form['complaint_type']
        department = request.form['department']
        description = request.form['description']
        category = classifier.predict(description)
        
        new_complaint = Complaint(
            complaint_type=complaint_type,
            department=department,
            description=description,
            category=category,
            user_id=session['user_id'],
            status='Pending',
            created_at=datetime.utcnow()
        )
        db.session.add(new_complaint)
        db.session.commit()
        
        flash(f'Complaint submitted successfully! Category: {category}')
        return redirect(url_for('dashboard'))
    
    return render_template('submit_complaint.html')

@app.route('/update_status/<int:complaint_id>', methods=['POST'])
def update_status(complaint_id):
    if 'user_id' not in session or session['role'] not in ['officer', 'it']:
        flash('Unauthorized access.')
        return redirect(url_for('login'))
    
    complaint = Complaint.query.get_or_404(complaint_id)
    new_status = request.form['status']
    complaint.status = new_status
    db.session.commit()
    
    flash('Complaint status updated.')
    return redirect(url_for('officer_dashboard' if session['role'] == 'officer' else 'it_dashboard'))

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user_message = request.form['message']
        response = process_chatbot_message(user_message, session['user_id'])
        return jsonify({'response': response})
    return render_template('chatbot.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
