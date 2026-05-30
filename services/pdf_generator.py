import os
from weasyprint import HTML
from .engine import get_student_final_results

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_student_pdf(student_id, output_filename):
    data = get_student_final_results(student_id)
    if not data: return False
    
    p = data['profile']
    subs = data['subjects']
    m = data['metrics']
    
    rows = "".join([f"<tr><td>{s['code']}</td><td>{s['title']}</td><td>{s['max']}</td><td>{s['obt']}</td><td>{s['grade']}</td></tr>" for s in subs])
    
    html = f"""
    <html>
    <head><style>
        body {{ font-family: sans-serif; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #333; padding: 8px; text-align: center; }}
    </style></head>
    <body>
        <h1>APEX INTERNATIONAL UNIVERSITY</h1>
        <p><strong>Name:</strong> {p['name']} | <strong>Enrollment:</strong> {p['enrollment']}</p>
        <table>
            <tr><th>Code</th><th>Subject</th><th>Max</th><th>Obtained</th><th>Grade</th></tr>
            {rows}
        </table>
        <p><strong>Percentage:</strong> {m['percentage']}% | <strong>Status:</strong> {m['status']}</p>
    </body>
    </html>
    """
    
    path = os.path.join(BASE_DIR, "exports", output_filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    HTML(string=html).write_pdf(path)
    return True