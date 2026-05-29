from bson.objectid import ObjectId
from core.database import get_db

def add_class(class_name, section):
    """Inserts a new class container with an empty embedded array for subjects."""
    db = get_db()
    new_class = {
        "class_name": class_name,
        "section": section.upper(),
        "subjects": []
    }
    result = db.classes.insert_one(new_class)
    return result.inserted_id

def delete_class_by_id(class_id):
    """Removes a class document from MongoDB."""
    db = get_db()
    db.classes.delete_one({"_id": ObjectId(class_id)})
    # Optional cleanup: Orphaned students belonging to this class can be left or handled.

def add_subject_to_class(class_id, code, title, max_marks):
    """Appends a custom subject dictionary item inside the target class document array."""
    db = get_db()
    subject_data = {
        "id": str(ObjectId()),
        "code": code.upper().strip(),
        "title": title.strip(),
        "max_marks": int(max_marks)
    }
    db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {"$push": {"subjects": subject_data}}
    )
    return subject_data["id"]

def add_student(enrollment_no, name, class_id):
    """Registers a student profile pointing structurally to an assigned class group."""
    db = get_db()
    new_student = {
        "enrollment_no": enrollment_no.upper().strip(),
        "name": name.strip(),
        "class_id": str(class_id)
    }
    if db.students.find_one({"enrollment_no": new_student["enrollment_no"]}):
        return None
    result = db.students.insert_one(new_student)
    return result.inserted_id

def delete_student_by_id(student_id):
    """Deletes a student record and drops their associated marks cards."""
    db = get_db()
    # 1. Clear out the student profile doc
    db.students.delete_one({"_id": ObjectId(student_id)})
    # 2. Drop any marks linked to this specific student string ID
    db.marks.delete_many({"student_id": str(student_id)})

def enter_or_update_marks(student_id, subject_id, marks_obtained):
    """Upserts grade records into the marks collection."""
    db = get_db()
    db.marks.update_one(
        {"student_id": str(student_id), "subject_id": str(subject_id)},
        {"$set": {"marks_obtained": float(marks_obtained)}},
        upsert=True
    )