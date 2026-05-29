import os
from flask import Flask, render_template, request, redirect, send_file, abort
from bson.objectid import ObjectId
from core.database import get_db
from services.crud import (
    add_class, delete_class_by_id, add_subject_to_class, 
    add_student, delete_student_by_id, enter_or_update_marks
)
from services.pdf_generator import generate_student_pdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "web", "templates"))

@app.route('/')
def dashboard():
    db = get_db()
    classes = list(db.classes.find().sort([("class_name", 1), ("section", 1)]))
    class_map = {str(c["_id"]): f"{c['class_name']} - Sec {c['section']}" for c in classes}
    
    students_cursor = db.students.find()
    students = []
    for s in students_cursor:
        s_dict = dict(s)
        s_dict["id"] = str(s_dict["_id"])
        s_dict["class_display"] = class_map.get(s_dict["class_id"], "Unknown Class")
        students.append(s_dict)
        
    return render_template("dashboard.html", students=students, classes=classes)

@app.route('/add_class', methods=['POST'])
def handle_add_class():
    name = request.form.get('class_name')
    sec = request.form.get('section')
    if name and sec: add_class(name, sec)
    return redirect('/')

@app.route('/delete_class/<class_id>', methods=['POST'])
def handle_delete_class():
    delete_class_by_id(class_id)
    return redirect('/')

@app.route('/add_subject', methods=['POST'])
def handle_add_subject():
    c_id = request.form.get('class_id')
    code = request.form.get('code')
    title = request.form.get('title')
    max_m = request.form.get('max_marks')
    if c_id and code and title and max_m:
        add_subject_to_class(c_id, code, title, int(max_m))
    return redirect('/')

@app.route('/add_student', methods=['POST'])
def handle_add_student():
    name = request.form.get('name')
    enroll = request.form.get('enrollment_no')
    c_id = request.form.get('class_id')
    if name and enroll and c_id: add_student(enroll, name, c_id)
    return redirect('/')

@app.route('/delete_student/<student_id>', methods=['POST'])
def handle_delete_student(student_id):
    delete_student_by_id(student_id)
    return redirect('/')

@app.route('/clear_all_subjects', methods=['POST'])
def clear_all_subjects():
    db = get_db()
    db.classes.update_many({}, {"$set": {"subjects": []}})
    db.marks.delete_many({})
    return redirect('/')

@app.route('/clear_all_marks', methods=['POST'])
def clear_all_marks():
    db = get_db()
    db.marks.delete_many({})
    return redirect('/')

@app.route('/student/<student_id>/marks')
def manage_student_marks(student_id):
    db = get_db()
    student = db.students.find_one({"_id": ObjectId(student_id)})
    if not student: abort(404)
    class_doc = db.classes.find_one({"_id": ObjectId(student["class_id"])})
    
    marks_map = {m["subject_id"]: m["marks_obtained"] for m in db.marks.find({"student_id": str(student_id)})}
    
    subjects = []
    if class_doc and "subjects" in class_doc:
        for sub in class_doc["subjects"]:
            sub_dict = dict(sub)
            sub_dict["marks_obtained"] = marks_map.get(sub["id"], "")
            subjects.append(sub_dict)
        
    profile = {"id": str(student["_id"]), "name": student["name"], "enrollment_no": student["enrollment_no"]}
    return render_template("manage_marks.html", student=profile, subjects=subjects)

@app.route('/student/<student_id>/save_marks', methods=['POST'])
def save_student_marks(student_id):
    for key, value in request.form.items():
        if key.startswith('marks_') and value.strip() != '':
            sub_id = key.split('_')[1]
            enter_or_update_marks(student_id, sub_id, float(value))
    return redirect('/')

@app.route('/download/<student_id>')
def download_pdf(student_id):
    pdf_name = f"Result_Student_{student_id}.pdf"
    if generate_student_pdf(student_id, pdf_name):
        return send_file(os.path.join(BASE_DIR, "exports", pdf_name), as_attachment=True)
    abort(404, "Generation error.")