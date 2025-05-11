from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from gridfs import GridFS
import os
import logging
import re
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more detailed output
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Set Secret Key
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")

# CSRF Protection
csrf = CSRFProtect(app)

# Configure file upload settings
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Create upload directory

client=MongoClient("mongodb://localhost:27017/")
db=client["HireSmartDB"]
recruiters_collection = db["Recruiters"]
jobs_collection = db["Jobs"]
signup_collection = db["Signup"]  # Collection to store signup details
job_applicant_collection = db["JobApplicant"]  # Collection for applicant details
fs = GridFS(db)  # GridFS for storing resume files

# Validate email format
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

# Validate password strength
def is_strong_password(password):
    return bool(re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password))

# Validate file uploads
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx'}

# Home Page
@app.route('/')
def home():
    return render_template('hiresmart.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Handle form data if needed
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # Add logic for storing or processing data
        if name and email and message:
            flash("Thank you for reaching out! We'll get back to you soon.",  "success")
        else:
            flash("All fields are required!", "danger")
        return redirect(url_for('contact'))

    return render_template('contact.html')

# Recruiter Signup
@app.route('/recruiter_signup', methods=['GET', 'POST'])
def recruiter_signup():
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        password = request.form.get('password')
        role = "Recruiter"  # Static role for recruiters
        
        # Validate required fields
        if not full_name or not email or not password:
            print("All fields are required!", "danger")
            return redirect(url_for('recruiter_signup'))

        # Check if email is valid
        if not is_valid_email(email):
            print("Please enter a valid email address.", "danger")
            return redirect(url_for('recruiter_signup'))

        # Check if email is already registered
        if signup_collection.find_one({'email': email}):
            print("Email already registered!", "danger")
            return redirect(url_for('recruiter_signup'))

        # Check if password is strong
        if not is_strong_password(password):
            print("Password must be strong (at least 8 characters, with uppercase, lowercase, number, and special character).", "danger")
            return redirect(url_for('recruiter_signup'))
        print("hi")

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Insert details into the database
        try:
            result = signup_collection.insert_one({
                'full_name': full_name,
                'email': email,
                'password': hashed_password,
                'role': role
            })

            # Log the inserted ID and count the total rows in the collection
            if result.inserted_id:
                print(f"Document inserted with ID: {result.inserted_id}")
            else:
                print("Insert operation failed.")

            # Count documents in the Signup collection
            total_documents = signup_collection.count_documents({})
            print(f"Total documents in Signup collection: {total_documents}")

            flash(f"Signup successful! Welcome, {full_name}", "success")
            return redirect(url_for('recruiter_login'))  # Redirect to login page

        except Exception as e:
            print(f"Error inserting document into MongoDB: {str(e)}")
            flash("An error occurred while signing up. Please try again.", "danger")
            return redirect(url_for('recruiter_signup'))

    return render_template('recruiter_signup.html')



# Applicant Signup
@app.route('/applicant_signup', methods=['GET', 'POST'])
def applicant_signup():
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        password = request.form.get('password')
        role = "JobApplicant"  # Static role for applicants

        print(f"Received Signup Request: {full_name}, {email}")  # Debugging

        # Validate required fields
        if not full_name or not email or not password:
            print("Error: All fields are required!")
            flash("All fields are required!", "danger")
            return redirect(url_for('applicant_signup'))

        # Check if email is valid
        if not is_valid_email(email):
            print("Error: Invalid Email Address!")
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for('applicant_signup'))

        # Check if email is already registered
        if signup_collection.find_one({'email': email}):
            print("Error: Email Already Registered!")
            flash("Email already registered!", "danger")
            return redirect(url_for('applicant_signup'))

        # Check if password is strong
        if not is_strong_password(password):
            print("Error: Weak Password!")
            flash("Password must be strong (at least 8 characters, with uppercase, lowercase, number, and special character).", "danger")
            return redirect(url_for('applicant_signup'))
        try:
        # Hash the password
            hashed_password = generate_password_hash(password)
        
        except Exception as e:
            print(f"Error Hashing Password: {e}")
            flash("Error processing password!", "danger")
            return redirect(url_for('applicant_signup'))

        
    
        # Insert details into the database
        try:
            result= signup_collection.insert_one({
                'full_name': full_name,
                'email': email,
                'password': hashed_password,
                'role': role
        })

            print(f"Signup successful! Inserted ID: {result.inserted_id}")
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for('applicant_login'))  # Redirect to login page
        except Exception as e:
            print(f"Database Error: {e}")
            flash("Error saving data! Try again later.", "danger")
            return redirect(url_for('applicant_signup'))

    return render_template('applicant_signup.html')


@app.route('/recruiter/login', methods=['GET', 'POST'])
def recruiter_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Find recruiter in the database
        recruiter = signup_collection.find_one({'email': email, 'role': 'Recruiter'})

        if recruiter and check_password_hash(recruiter['password'], password):
            # Set session variables
            session['user_id'] = str(recruiter['_id'])
            session['user_name'] = recruiter['full_name']
            session['role'] = recruiter['role']

            # Redirect to recruiter dashboard
            return redirect(url_for('recruiter_dashboard'))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('recruiter_login'))

    return render_template('recruiter_login.html')

# Applicant Login
@app.route('/applicant/login', methods=['GET', 'POST'])
def applicant_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        print(f"Email: {email}, Password: {password}")  # Debugging

        applicant = signup_collection.find_one({'email': email, 'role': "JobApplicant"})

        print(f"Applicant: {applicant}")  # Debugging

        if applicant and check_password_hash(applicant['password'], password):
            session['user_id'] = str(applicant['_id'])
            session['user_name'] = applicant['full_name']
            session['role'] = applicant['role']
            
            print(f"Session after login: {session}")  # Debugging
            flash(f"Welcome {session['user_name']}!", "success")
            return redirect(url_for('applicant_dashboard'))
        else:
            flash("Invalid credentials!", "danger")
            return redirect(url_for('applicant_login'))
        
    return render_template('applicant_login.html')

@app.route('/recruiter/dashboard')
def recruiter_dashboard():
    if 'user_id' in session and session['role'] == 'Recruiter':
        return render_template('recruiter_dashboard.html', recruiter_name=session['user_name'])
    else:
        flash("Unauthorized access. Please log in as a recruiter.", "danger")
        return redirect(url_for('recruiter_login'))

# Applicant Dashboard
@app.route('/applicant/dashboard')
def applicant_dashboard():
    if 'user_id' in session and session['role'] == 'JobApplicant':
        return render_template('applicant_dashboard.html', user_name=session['user_name'])
    else:
        flash("Unauthorized access. Please log in as a Jobapplicant.", "danger")
        return redirect(url_for('applicant_login'))

@app.route("/post_job", methods=["POST"])
def post_job():
    if 'user_id' not in session or session['role'] != 'Recruiter':
        flash("Unauthorized access. Only recruiters can post jobs.", "danger")
        return redirect(url_for('recruiter_login'))

    if request.method == "POST":
        try:
        # Retrieve form data
            job_data = {
                "jobTitle": request.form["jobTitle"],
                "jobSummary": request.form["jobSummary"],
                "location": request.form["location"],
                "companyName": request.form["companyName"],
                "qualifications": request.form["qualifications"],
                "noOfCandidates": int(request.form["noOfCandidates"]),
                "responsibilities": request.form["responsibilities"],
                "skills": request.form["skills"],
                "experience": request.form["experience"],
                "education": request.form["education"],
                "jobType": request.form["jobType"],
                "compensation": request.form["compensation"],
                "workSchedule": request.form["workSchedule"],
                "remoteOptions": request.form["remoteOptions"],
                "deadline": request.form["deadline"],
                "applicationProcess": request.form["applicationProcess"],
                "pointOfContact": request.form["pointOfContact"],
                "posted_by": ObjectId(session['user_id']),
                "posted_at": datetime.now()
                
            }
        
            # Insert into MongoDB Jobs collection
            result = jobs_collection.insert_one(job_data)
            logger.info(f"Job posted successfully with ID: {result.inserted_id}")
            flash("Job posted successfully!", "success")
            return redirect(url_for("recruiter_dashboard"))
        
        except KeyError as e:
            logger.error(f"Missing form field: {e}")
            flash(f"Error: Missing required field {e}", "danger")
            return redirect(url_for("recruiter_dashboard"))
        except Exception as e:
            logger.error(f"Error posting job: {e}")
            flash(f"Error posting job: {str(e)}", "danger")
            return redirect(url_for("recruiter_dashboard"))
    
@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/logout')
def logout():
    # Check the user's role before clearing the session
    if 'role' in session:
        role = session['role']
        session.clear()  # Clear the session
        flash("Logged out successfully.", "info")

        # Redirect based on the user's role
        if role == 'Recruiter':
            return redirect(url_for('recruiter_login'))
        elif role == 'JobApplicant':
            return redirect(url_for('applicant_login'))
    
    # If no role is found, redirect to a default page (e.g., home)
    return redirect(url_for('home'))

# Personal Information Route
@app.route('/profile_settings', methods=['GET', 'POST'])
def profile_settings():
    if 'user_id' not in session or session['role'] != 'JobApplicant':
        logger.error("Unauthorized access to profile_settings")
        flash("Please login as an applicant first", "danger")
        return redirect(url_for('applicant_login'))

    applicant_id = ObjectId(session['user_id'])
    logger.debug(f"Profile settings accessed by applicant_id: {applicant_id}")

    if request.method == 'POST':
        logger.debug(f"Received POST request to /profile_settings: {request.form}")
        try:
            personal_info = {
                'firstName': request.form.get('firstName', ''),
                'lastName': request.form.get('lastName', ''),
                'fullName': request.form.get('fullName', ''),
                'phone': request.form.get('phone', ''),
                'nationality': request.form.get('nationality', ''),
                'gender': request.form.get('gender', ''),
                'dob': request.form.get('dob', ''),
                'address': {
                    'line1': request.form.get('addressLine1', ''),
                    'line2': request.form.get('addressLine2', ''),
                    'country': request.form.get('country', ''),
                    'city': request.form.get('city', ''),
                    'state': request.form.get('state', ''),
                    'zipCode': request.form.get('zipCode', '')
                }
            }
            
            logger.debug(f"Personal info to save: {personal_info}")
            session["personal_data"] = personal_info
            logger.debug(f"Session after setting personal_data: {session}")
            return redirect(url_for('education_qualifications'))
        
        except Exception as e:
            logger.error(f"Personal info save error: {str(e)}", exc_info=True)
            flash(f"Error saving personal details: {str(e)}", "danger")            
            return redirect(url_for('profile_settings'))

    # Load existing data for GET request
    existing_data = job_applicant_collection.find_one({"_id": applicant_id})
    logger.debug(f"Existing data for applicant_id {applicant_id}: {existing_data}")
    return render_template('profile_settings.html', 
                        data=existing_data.get('personal_info', {}) if existing_data else {})
    
@app.route('/applied_jobs')
def applied_jobs():
    # Logic to fetch applied jobs
    return render_template("applied_jobs.html")

# Education Qualifications
@app.route('/education_qualifications', methods=['GET', 'POST'])
def education_qualifications():
    if 'user_id' not in session or session['role'] != 'JobApplicant':
        logger.error("Unauthorized access to education_qualifications")
        flash("Please login as applicant first", "danger")
        return redirect(url_for('applicant_login'))

    applicant_id = ObjectId(session['user_id'])
    logger.debug(f"Education qualifications accessed by applicant_id: {applicant_id}")

    if request.method == 'POST':
        logger.debug(f"Received POST request to /education_qualifications: {request.form}")
        try:
            # Handle file upload
            resume = request.files.get('resume')
            resume_file_id = None
            
            if resume and resume.filename != '':
                if not allowed_file(resume.filename):
                    logger.error(f"Invalid file type for resume: {resume.filename}")
                    flash("Invalid file type for resume", "danger")
                    return redirect(url_for('education_qualifications'))
                
                resume_file_id = fs.put(
                    resume,
                    filename=secure_filename(f"{applicant_id}_{resume.filename}"),
                    content_type=resume.content_type
                )
                logger.debug(f"Resume uploaded to GridFS with file_id: {resume_file_id}")

            # Convert active backlogs to integer safely
            try:
                active_backlogs = int(request.form.get('activeBacklogs', 0))
            except ValueError:
                active_backlogs = 0

            # Education data structure
            education_data = {
                "applying_for": request.form.get('applyingFor', ''),
                "highest_qualification": request.form.get('highestQualification', ''),
                "completion_year": request.form.get('completionYear', ''),
                "ug_course_type": request.form.get('ugCourseType', ''),  # Added from your form
                "tenth_marks": request.form.get('tenthMarks', ''),
                "tenth_year": request.form.get('tenthYear', ''),
                "higher_secondary": request.form.get('higherSecondary', ''),
                "ug_degree": request.form.get('ugDegree', ''),
                "ug_specialization": request.form.get('ugSpecialization', ''),
                "ug_marks": request.form.get('ugMarks', ''),
                "active_backlogs": active_backlogs,
                "pg_college": request.form.get('pgCollege', ''),  # Added from your form
                "pg_year": request.form.get('pgYear', ''),  # Added from your form
                "work_experience": request.form.get('workExperience', ''),
                "semester_exams": request.form.get('semesterExams', ''),
                "resume_file_id": str(resume_file_id) if resume_file_id else None
            }
            
            logger.debug(f"Education data to save: {education_data}")

        # If part of job application, store in session and redirect to agreement
            if "applying_job_id" in session:
                job_id = ObjectId(session["applying_job_id"])
                personal_data = session.get("personal_data", {})

                # Prepare the application data
                application_data = {
                    "job_id": job_id,
                    "applied_at": datetime.utcnow(),
                    "status": "Pending"
                }
            
                result = job_applicant_collection.update_one(
                    {"_id": applicant_id},
                    {
                        "$set": {
                        "personal_info": personal_data,
                        "education": education_data
                        },
                        "$push": {
                            "applied_jobs": application_data
                        }
                    },
                    upsert=True
                )

                if result.modified_count > 0 or result.upserted_id:
                    logger.info(f"Job application submitted for applicant_id: {applicant_id}, job_id: {job_id}")
                    flash("Your application has been submitted successfully!", "success")
                else:
                    logger.warning(f"No changes detected for applicant_id: {applicant_id}")
                    flash("No changes detected in application", "info")

                # Clear session data after submission
                session.pop("applying_job_id", None)
                session.pop("personal_data", None)
                logger.debug(f"Session after clearing: {session}")
                return redirect(url_for('applied_jobs'))
            # Otherwise, save education data directly
            else:
                result = job_applicant_collection.update_one(
                    {"_id": applicant_id},
                    {"$set": {"education": education_data}},
                    upsert=True
                )

                if result.modified_count > 0:
                    logger.info(f"Education details updated for applicant_id: {applicant_id}")
                    flash("Education details updated successfully!", "success")
                elif result.upserted_id:
                    logger.info(f"Education details inserted for applicant_id: {applicant_id}, upserted_id: {result.upserted_id}")
                    flash("Education details saved successfully!", "success")
                elif resume_file_id:
                    logger.info(f"Resume updated for applicant_id: {applicant_id}")
                    flash("Resume updated successfully!", "success")
                else:
                    logger.info(f"No changes detected for applicant_id: {applicant_id}")
                    flash("No changes detected", "info")
                return redirect(url_for('applicant_dashboard'))
        
        except Exception as e:
            logger.error(f"Education save error: {str(e)}", exc_info=True)
            flash(f"Error saving education details: {str(e)}", "danger")            
            return redirect(url_for('education_qualifications'))

    # Load existing data
    existing_data = job_applicant_collection.find_one({"_id": applicant_id})
    logger.debug(f"Existing data for applicant_id {applicant_id}: {existing_data}")
    return render_template('education_qualifications.html', 
                    data=existing_data.get('education', {}) if existing_data else {})
    
@app.route("/job_openings")
def job_openings():
    if 'user_id' not in session or session['role'] != 'JobApplicant':
        flash("Unauthorized access. Please log in as a job applicant.", "danger")
        return redirect(url_for('applicant_login'))
    
    # Fetch all job postings from the Jobs collection
    jobs = list(jobs_collection.find())
    
    return render_template("job_openings.html", jobs=jobs)

@app.route('/apply_job/<job_id>', methods=['POST'])
def apply_job(job_id):
    if 'user_id' not in session or session['role'] != 'JobApplicant':
        flash("Please login as an applicant first", "danger")
        return redirect(url_for('applicant_login'))

    try:
        applicant_id = ObjectId(session['user_id'])
        job_id = ObjectId(job_id)

        # Check if the applicant has already applied for this job
        existing_application = job_applicant_collection.find_one({
            "_id": applicant_id,
            "applied_jobs.job_id": job_id
        })
        if existing_application:
            flash("You have already applied for this job!", "warning")
            return redirect(url_for("job_openings"))

        # Store the job_id in session to indicate we're in the application process
        session["applying_job_id"] = str(job_id)
        return redirect(url_for("profile_settings"))
    
    except Exception as e:
        logger.error(f"Error initiating job application: {str(e)}")
        flash(f"Error applying for job: {str(e)}", "danger")
        return redirect(url_for("job_openings"))

@app.route("/candidates")
def candidates():
    applicants = list(job_applicant_collection.find())  # Convert to list to pass into template
    return render_template("candidates.html", applicants=applicants)

@app.route("/upload_resume", methods=["GET", "POST"])
def upload_resume():
    if 'user_id' not in session or session['role'] != 'JobApplicant':
        flash("Please log in as an applicant first.", "danger")
        return redirect(url_for('applicant_login'))

    applicant_id = ObjectId(session['user_id'])

    if request.method == "POST":
        resume = request.files.get("resume")
        photo = request.files.get("photo")

        try:
            if resume and allowed_file(resume.filename):
                resume_file_id = fs.put(
                    resume,
                    filename=secure_filename(f"{applicant_id}_{resume.filename}"),
                    content_type=resume.content_type
                )
                job_applicant_collection.update_one(
                    {"_id": applicant_id},
                    {"$set": {"resume_file_id": str(resume_file_id)}},
                    upsert=True
                )
            else:
                flash("Please upload a valid resume file (PDF, DOC, DOCX).", "danger")
                return redirect(url_for("upload_resume"))

            if photo and photo.filename.endswith((".jpg", ".png", ".jpeg")):
                photo_file_id = fs.put(
                    photo,
                    filename=secure_filename(f"{applicant_id}_{photo.filename}"),
                    content_type=photo.content_type
                )
                job_applicant_collection.update_one(
                    {"_id": applicant_id},
                    {"$set": {"photo_file_id": str(photo_file_id)}},
                    upsert=True
                )
            elif photo:
                flash("Please upload a valid photo file (JPG, PNG, JPEG).", "danger")
                return redirect(url_for("upload_resume"))

            flash("Files uploaded successfully!", "success")
            return redirect(url_for("upload_resume"))

        except Exception as e:
            logger.error(f"Error uploading files: {str(e)}")
            flash(f"Error uploading files: {str(e)}", "danger")
            return redirect(url_for("upload_resume"))

    # Render the upload form for GET request
    return render_template("upload_resume.html")

@app.route("/resumes")
def resumes():
    return render_template("resumes.html", candidates=candidates)

if __name__ == '__main__':
    app.run(debug=True)
