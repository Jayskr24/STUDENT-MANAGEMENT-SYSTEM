import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from core.database import get_db
from services.pdf_generator import generate_student_pdf
from flask import send_from_directory

# Sahi absolute configuration paths (kyunki app.py 'web/' folder ke andar hai)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(BASE_DIR, 'web', 'templates')
static_dir = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_key_change_this_later")

# ==========================================
# 🔐 FLASK-LOGIN & SESSION CONFIGURATION
# ==========================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user_data = db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# ==========================================
# 🔑 SECURITY & AUTHENTICATION ROUTES
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            flash("Please fill in all fields.", "warning")
            return redirect(url_for("register"))
            
        db = get_db()
        if db.users.find_one({"username": username}):
            flash("Username already taken! Please try another.", "danger")
            return redirect(url_for("register"))
            
        hashed_password = generate_password_hash(password)
        db.users.insert_one({
            "username": username,
            "password": hashed_password
        })
        flash("Registration successful! Please login here.", "success")
        return redirect(url_for("login"))
        
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        db = get_db()
        user_data = db.users.find_one({"username": username})
        
        if user_data and check_password_hash(user_data["password"], password):
            user_obj = User(user_data)
            login_user(user_obj)
            return redirect(url_for("dashboard"))
            
        flash("Invalid username or password. Please try again.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


# ==========================================
# 🧭 SEPARATE INTERFACE ROUTES WITH NAVIGATION
# ==========================================

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# 1. Main Landing Summary Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# 2. Separate Interface for Class Configuration
@app.route("/manage_classes", methods=["GET", "POST"])
@login_required
def manage_classes():
    db = get_db()
    if request.method == "POST":
        grade = request.form.get("grade", "").strip()
        section = request.form.get("section", "").strip()
        
        if grade and section:
            class_id = f"{grade}-{section}"
            if not db.classes.find_one({"class_id": class_id}):
                db.classes.insert_one({"class_id": class_id, "grade": grade, "section": section})
                flash(f"Class {class_id} added successfully!", "success")
            else:
                flash("Class configuration already exists!", "warning")
        return redirect(url_for("manage_classes"))

    classes = list(db.classes.find())
    return render_template("classes.html", classes=classes)

# 🔥 CLASS WIPE OUT (DELETE) ROUTE
@app.route("/delete_class/<path:class_id>", methods=["POST"])
@login_required
def delete_class(class_id):
    print(f"DEBUG: Server ko mili ID: {class_id}") # Terminal mein ye print dekho
    db = get_db()
    result = db.classes.delete_one({"class_id": class_id})
    return ("Success", 200) if result.deleted_count > 0 else ("Not Found", 404)

# 📝 CLASS DATA UPDATE ROUTE
@app.route("/update_class/<path:class_id>", methods=["POST"])
@login_required
def update_class(class_id):
    db = get_db()
    new_grade = request.form.get("edit_grade")
    new_section = request.form.get("edit_section")
    # Update command
    db.classes.update_one(
        {"class_id": class_id}, 
        {"$set": {"grade": new_grade, "section": new_section, "class_id": f"{new_grade}-{new_section}"}}
    )
    return redirect(url_for("manage_classes"))

@app.route("/add_marks/<enrollment_no>", methods=["POST"])
@login_required
def add_marks(enrollment_no):
    db = get_db()
    subject = request.form.get("subject")
    marks = request.form.get("marks")
    
    # MongoDB mein marks update karne ka logic
    db.students.update_one(
        {"enrollment_no": enrollment_no},
        {"$push": {"marks_list": {"subject": subject, "marks": marks}}}
    )
    
    flash("Marks added successfully!", "success")
    return redirect(url_for('student_marks', enrollment_no=enrollment_no))

@app.route("/update_marks/<enrollment_no>", methods=["POST"])
@login_required
def update_marks(enrollment_no):
    db = get_db()
    subject = request.form.get("subject")
    new_marks = request.form.get("new_marks")
    
    # MongoDB mein specific subject ke marks update karna
    db.students.update_one(
        {"enrollment_no": enrollment_no, "marks_list.subject": subject},
        {"$set": {"marks_list.$.marks": new_marks}}
    )
    
    flash("Marks updated!", "success")
    return redirect(url_for('student_marks', enrollment_no=enrollment_no))


@app.route("/delete_marks/<enrollment_no>", methods=["POST"])
@login_required
def delete_marks(enrollment_no):
    db = get_db()
    subject_to_delete = request.form.get("subject")
    
    # MongoDB pull operator use karenge
    db.students.update_one(
        {"enrollment_no": enrollment_no},
        {"$pull": {"marks_list": {"subject": subject_to_delete}}}
    )
    
    flash(f"Marks for {subject_to_delete} deleted!", "success")
    return redirect(url_for('student_marks', enrollment_no=enrollment_no))

# 3. Separate Interface for Student Directory 
@app.route("/manage_students", methods=["GET", "POST"])
@login_required
def manage_students():
    db = get_db()
    if request.method == "POST":
        enrollment_no = request.form.get("enrollment_no", "").strip()
        name = request.form.get("name", "").strip()
        class_id = request.form.get("class_id", "").strip()
        
        if enrollment_no and name and class_id:
            if not db.students.find_one({"enrollment_no": enrollment_no.upper()}):
                db.students.insert_one({
                    "enrollment_no": enrollment_no.upper(),
                    "name": name,
                    "class_id": class_id
                })
                flash(f"Student {name} registered successfully!", "success")
            else:
                flash("Enrollment number already exists!", "danger")
        return redirect(url_for("manage_students"))

    classes = list(db.classes.find())
    students = list(db.students.find())
    for s in students:
        s['id'] = str(s['_id'])
    return render_template("students.html", students=students, classes=classes)

# 4. Separate Interface for PDF Marks Report Downloads
@app.route("/download_center")
@login_required
def download_center():
    db = get_db()
    # Saare students fetch karein
    students = list(db.students.find())
    
    # IMPORTANT: Har student dictionary mein 'id' key add karein
    # Kyunki database mein '_id' hota hai (jo ObjectId hai), 
    # HTML template mein use string bana kar bhejna padega.
    for s in students:
        s['id'] = str(s['_id']) 
        
    return render_template("downloads.html", students=students)
# ==========================================
# ⚙️ SYSTEM ACTIONS & OPERATIONS 
# ==========================================

# ... (Baaki sab same rakhein, bas niche diye gaye routes replace karein)

# 🔥 STUDENT DELETE ROUTE (Corrected)
@app.route("/delete_student/<path:enrollment_no>", methods=["POST"])
@login_required
def delete_student(enrollment_no):
    db = get_db()
    # MongoDB mein enrollment_no save hai, wahi use karenge
    result = db.students.delete_one({"enrollment_no": enrollment_no})
    
    if result.deleted_count > 0:
        return "Success", 200
    return "Not Found", 404

# 📝 MARKS ROUTE (Missing Route Fixed)
# Aapke code mein link `/student/{{ student.enrollment_no }}/marks` tha
# Toh route bhi waisa hi hona chahiye:
@app.route("/student/<enrollment_no>/marks")
@login_required
def student_marks(enrollment_no):
    db = get_db()
    student = db.students.find_one({"enrollment_no": enrollment_no})
    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for("manage_students"))
    return render_template("marks.html", student=student)
    
    # Yahan 'marks.html' render hoga
    return render_template("marks.html", student=student)
# PDF Generation Trigger Point
# web/app.py (ensure imports are at the top)

@app.route('/download/<student_id>')
@login_required
def download_pdf(student_id):
    filename = f"Report_{student_id}.pdf"
    # Nayi generate function ko call karein
    success = generate_student_pdf(student_id, filename)
    
    if success:
        # File path sahi hona chahiye
        return send_from_directory(os.path.join(BASE_DIR, 'exports'), filename)
    else:
        return "PDF Generation Failed", 500