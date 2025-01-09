from flask import Flask, render_template, request, redirect, url_for, flash, session 
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Set Secret Key
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
try:
    client = MongoClient(MONGO_URI)
    db = client['HireSmartDB']  # Database name
except Exception as e:
    logging.error(f"Error connecting to MongoDB: {str(e)}")
    raise SystemExit("Failed to connect to MongoDB. Please check the connection string and database server.")

recruiters_collection = db['Recruiters']
candidates_collection = db['JobApplicant']

# Home Page
@app.route('/')
def home():
    return render_template('hiresmart.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

# Contact Page
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # You can handle storing the message or sending it via email here
        # For now, just log the message
        if name and email and message:
            logging.info(f"Message received from {name} ({email}): {message}")
            flash("Your message has been sent!", "success")
        else:
            flash("All fields are required!", "danger")
        return redirect(url_for('home'))  # Redirect to home or another page after submission

    return render_template('contact.html')
# Password Strength Validation
def is_strong_password(password):
    return bool(re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password))

# Recruiter Registration
@app.route('/recruiter/register', methods=['GET', 'POST'])
def recruiter_register():
    if request.method == 'POST':
        company_name = request.form.get('companyName')
        job_description = request.form.get('jobDescription')
        salary_package = request.form.get('salaryPackage')
        job_type = request.form.get('jobType')
        application_deadline = request.form.get('applicationDeadline')
        num_candidates = request.form.get('numCandidates')
        qualifications = request.form.get('qualifications')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate password strength
        if not password or not is_strong_password(password):
            flash("Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.", "danger")
            return redirect(url_for('recruiter_register'))

        # Check for duplicate email
        if recruiters_collection.find_one({'email': email}):
            flash("Email already registered!", "danger")
            return redirect(url_for('recruiter_register'))

        # Hash the password before saving
        hashed_password = generate_password_hash(password)

        try:
            # Save to MongoDB
            recruiters_collection.insert_one({
                'company_name': company_name,
                'job_description': job_description,
                'salary_package': salary_package,
                'job_type': job_type,
                'application_deadline': application_deadline,
                'num_candidates': int(num_candidates),
                'qualifications': qualifications,
                'email': email,
                'password': hashed_password
            })
            flash("Recruiter registered successfully!", "success")
            logging.info(f"Recruiter {company_name} registered successfully.")
            return redirect(url_for('recruiter_login'))
        except Exception as e:
            logging.error(f"Error registering recruiter: {str(e)}")
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('recruiter_register'))

    return render_template('recruiter-register.html')

# Recruiter Login
@app.route('/recruiter/login', methods=['GET', 'POST'])
def recruiter_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Authenticate Recruiter
        recruiter = recruiters_collection.find_one({'email': email})
        if recruiter and check_password_hash(recruiter['password'], password):
            session['user_id'] = str(recruiter['_id'])  # MongoDB ID is ObjectId
            session['user_name'] = recruiter['company_name']
            flash(f"Welcome, {recruiter['company_name']}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials!", "danger")
    
    return render_template('recruiter-login.html')

# Applicant Registration
@app.route('/applicant/register', methods=['GET', 'POST'])
def applicant_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        address = request.form.get('address')
        github_link = request.form.get('github_link')
        resume_file = request.form.get('resume_file')
        status = "pending"  # Default status on registration
        # Validate password strength
        if not password or not is_strong_password(password):
            flash("Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.", "danger")
            return redirect(url_for('applicant_register'))

        # Check for duplicate email
        if candidates_collection.find_one({'email': email}):
            flash("Email already registered!", "danger")
            return redirect(url_for('applicant_register'))

        # Hash the password before saving
        hashed_password = generate_password_hash(password)

        try:
            # Save to MongoDB
            candidates_collection.insert_one({
                'name': name,
                'email': email,
                'password': hashed_password,
                'address': address,
                'github_link': github_link,
                'resume_file': resume_file,
                'status': status
            })
            flash("Applicant registered successfully!", "success")
            logging.info(f"Applicant {name} registered successfully.")
            return redirect(url_for('applicant_login'))
        except Exception as e:
            logging.error(f"Error registering applicant: {str(e)}")
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('applicant_register'))

    return render_template('applicant-register.html')

# Applicant Login
@app.route('/applicant/login', methods=['GET', 'POST'])
def applicant_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Authenticate Applicant
        applicant = candidates_collection.find_one({'email': email})
        if applicant and check_password_hash(applicant['password'], password):
            session['user_id'] = str(applicant['_id'])
            session['user_name'] = applicant['name']
            flash(f"Welcome, {applicant['name']}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials!", "danger")
    
    return render_template('applicant-login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
