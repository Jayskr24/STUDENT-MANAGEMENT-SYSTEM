import os
import sys

# Windows GTK Environment DLL Loader Patch Setup
GTK_FOLDER = r"C:\Program Files\GTK3-Runtime Win64\bin"
if os.path.exists(GTK_FOLDER):
    os.environ['PATH'] = GTK_FOLDER + os.pathsep + os.environ.get('PATH', '')
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(GTK_FOLDER)
        except Exception:
            pass

from weasyprint import HTML
from .engine import get_student_final_results

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_student_pdf(student_id, output_pdf_name):
    # Fetch consolidated student scores from the database engine wrapper
    data = get_student_final_results(str(student_id))
    if not data:
        return False

    profile = data["profile"]
    subjects = data["subjects"]
    metrics = data["metrics"]

    # Build up the dynamic HTML rows for each subject
    subject_rows_html = ""
    for sub in subjects:
        subject_rows_html += f"""
        <tr>
            <td>{sub['course_code']}</td>
            <td>{sub['subject_title']}</td>
            <td style="text-align: center;">{sub['max_marks']}</td>
            <td style="text-align: center;">{sub['marks_obtained']}</td>
            <td style="text-align: center; font-weight: bold; color: #2c5282;">{sub['letter_grade']}</td>
        </tr>
        """

    # Pure HTML template configured specifically for K-12 report cards
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 20mm 15mm; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #2d3748; line-height: 1.5; }}
            .header {{ border-bottom: 3px solid #2c5282; padding-bottom: 10px; margin-bottom: 25px; }}
            .institution-title {{ font-size: 22pt; font-weight: bold; color: #2c5282; letter-spacing: 0.5px; }}
            .report-title {{ font-size: 13pt; font-weight: bold; color: #4a5568; margin-top: 5px; }}
            
            .student-info-table {{ width: 100%; border-collapse: collapse; background: #f7fafc; border: 1px solid #e2e8f0; margin-bottom: 25px; }}
            .student-info-table td {{ padding: 10px 12px; font-size: 10pt; }}
            .info-label {{ font-weight: bold; color: #4a5568; width: 18%; }}
            
            .marks-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
            .marks-table th {{ background: #2c5282; color: white; padding: 10px; font-size: 10pt; text-transform: uppercase; }}
            .marks-table td {{ padding: 10px; border: 1px solid #e2e8f0; font-size: 10pt; }}
            .marks-table tr:nth-child(even) {{ background: #f8fafc; }}
            
            .summary-box {{ display: inline-block; width: 180px; border: 1px solid #cbd5e0; padding: 12px; margin-right: 15px; text-align: center; border-radius: 4px; background: #fff; }}
            .summary-label {{ font-size: 8pt; text-transform: uppercase; color: #718096; font-weight: bold; }}
            .summary-value {{ font-size: 16pt; font-weight: bold; color: #2b6cb0; margin-top: 4px; }}
            .PASSED {{ color: #38a169; }}
            .DETAINED {{ color: #e53e3e; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="institution-title">ST. XAVIER'S INTERNATIONAL SCHOOL</div>
            <div class="report-title">OFFICIAL REPORT CARD (ACADEMIC YEAR 2026)</div>
        </div>

        <table class="student-info-table">
            <tr>
                <td class="info-label">Student Name:</td><td><strong>{profile['student_name']}</strong></td>
                <td class="info-label">Enrollment No:</td><td>{profile['enrollment_no']}</td>
            </tr>
            <tr>
                <td class="info-label">Class Level:</td><td>{profile['class_name']}</td>
                <td class="info-label">Class Section:</td><td>Section {profile['section']}</td>
            </tr>
        </table>

        <table class="marks-table">
            <thead>
                <tr>
                    <th style="width: 15%;">Code</th>
                    <th style="text-align: left;">Subject Name</th>
                    <th style="width: 15%;">Max Marks</th>
                    <th style="width: 15%;">Obtained</th>
                    <th style="width: 15%;">Grade</th>
                </tr>
            </thead>
            <tbody>
                {subject_rows_html}
            </tbody>
        </table>

        <div>
            <div class="summary-box"><div class="summary-label">Aggregate Percentage</div><div class="summary-value">{metrics['percentage']}%</div></div>
            <div class="summary-box"><div class="summary-label">Final Grade Standing</div><div class="summary-value">{metrics['overall_grade']}</div></div>
            <div class="summary-box"><div class="summary-label">Result Status</div><div class="summary-value {metrics['status']}">{metrics['status']}</div></div>
        </div>
    </body>
    </html>
    """

    # Generate print rendering artifact buffers cleanly
    temp_html_path = os.path.join(BASE_DIR, "services", "temp_print.html")
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    output_pdf_path = os.path.join(BASE_DIR, "exports", output_pdf_name)
    try:
        HTML(temp_html_path).write_pdf(output_pdf_path)
        success = True
    except Exception as e:
        print(f"❌ WeasyPrint Rendering Failure: {e}")
        success = False
    finally:
        # Cleanup temporary scratchpad HTML file
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
            
    return success