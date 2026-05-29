from bson.objectid import ObjectId
from core.database import get_db

def calculate_letter_grade(percentage):
    if percentage >= 91: return 'A1'
    elif percentage >= 81: return 'A2'
    elif percentage >= 71: return 'B1'
    elif percentage >= 61: return 'B2'
    elif percentage >= 51: return 'C1'
    elif percentage >= 41: return 'C2'
    elif percentage >= 33: return 'D'
    else: return 'E'

def get_student_final_results(student_id):
    db = get_db()
    try:
        s_obj_id = ObjectId(student_id)
    except Exception:
        return None
        
    student = db.students.find_one({"_id": s_obj_id})
    if not student:
        return None
        
    class_doc = db.classes.find_one({"_id": ObjectId(student["class_id"])})
    if not class_doc:
        return None

    marks_cursor = db.marks.find({"student_id": str(student_id)})
    marks_map = {m["subject_id"]: m["marks_obtained"] for m in marks_cursor}

    subject_list = []
    total_max = 0
    total_obtained = 0

    for sub in class_doc.get("subjects", []):
        sub_id = sub["id"]
        obtained = marks_map.get(sub_id, None)
        
        if obtained is not None:
            pct = (obtained / sub["max_marks"]) * 100
            grade = calculate_letter_grade(pct)
            total_obtained += obtained
        else:
            grade = "N/A"
            
        total_max += sub["max_marks"]
        
        subject_list.append({
            "course_code": sub["code"],
            "subject_title": sub["title"],
            "max_marks": sub["max_marks"],
            "marks_obtained": obtained if obtained is not None else "-",
            "letter_grade": grade
        })

    percentage = (total_obtained / total_max) * 100 if total_max > 0 and total_obtained > 0 else 0
    
    return {
        "profile": {
            "student_name": student["name"],
            "enrollment_no": student["enrollment_no"],
            "class_name": class_doc["class_name"],
            "section": class_doc["section"]
        },
        "subjects": subject_list,
        "metrics": {
            "total_max": total_max,
            "total_obtained": total_obtained,
            "percentage": round(percentage, 2),
            "overall_grade": calculate_letter_grade(percentage) if total_obtained > 0 else "N/A",
            "status": "PASSED" if percentage >= 33 else "DETAINED"
        }
    }