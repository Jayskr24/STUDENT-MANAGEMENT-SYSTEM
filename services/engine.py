from bson import ObjectId
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
    # Student fetch
    student = db.students.find_one({"_id": ObjectId(student_id)})
    if not student: return None

    marks_list = student.get("marks_list", [])
    
    subject_list = []
    total_max = 0
    total_obt = 0
    
    # Directly marks_list se loop karein, kyuki database mein data yahi hai
    for m in marks_list:
        title = m.get("subject", "Unknown")
        obt = float(m.get("marks", 0))
        max_m = 100 # Default max marks
        
        total_max += max_m
        total_obt += obt
        
        subject_list.append({
            "code": "N/A",
            "title": title,
            "max": max_m,
            "obt": obt,
            "grade": calculate_letter_grade((obt/max_m)*100)
        })

    perc = (total_obt / total_max * 100) if total_max > 0 else 0
    
    return {
        "profile": {
            "name": student.get("name", "N/A"),
            "enrollment": student.get("enrollment_no", "N/A")
        },
        "subjects": subject_list,
        "metrics": {
            "percentage": round(perc, 2),
            "status": "PASSED" if perc >= 33 else "FAIL"
        }
    }