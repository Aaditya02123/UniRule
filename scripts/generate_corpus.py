import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# -----------------
# 1. ACADEMIC REGULATIONS (PDF)
# -----------------
ACADEMIC_REGULATIONS_TEXT = """
# TITLE: Medicaps University General Academic Regulations
## Section 1: Introduction and Scope
The academic regulations set forth the guidelines, principles, and rules governing all undergraduate and postgraduate academic activities at Medicaps University. These rules are binding on all enrolled students. The University firmly believes in maintaining a rigorous academic environment that fosters learning, discipline, and intellectual growth. All faculty members, administration staff, and students must familiarize themselves with this exhaustive document. The regulations apply to all faculties including Engineering, Arts, Business, and Science. Modifications to this document require approval from the University Senate. The Senate meets bi-annually to review and propose policy adjustments based on educational standards and institutional performance. The primary objective is to cultivate an internationally competitive academic atmosphere.

## Section 2: Registration and Enrollment
All students must complete their semester registration before the commencement of classes. Late registration is permitted up to two weeks after the start of the semester, subject to a late fee of 500 currency units. Students failing to register within this window will be automatically considered as taking a Leave of Absence. Registration requires the clearance of all prior financial dues, submission of required documentation, and approval from the academic advisor. The enrollment process integrates closely with the university portal. It is the responsibility of the student to ensure that their course load satisfies the prerequisite conditions and minimum credit bounds.

## Section 3: Attendance Requirements
Attendance is highly correlated with academic success and is thus mandatory. Medicaps University enforces strict classroom presence. The minimum attendance required for examination eligibility across all courses is explicitly set. Under no circumstances shall any student with less than 75% attendance be permitted to sit for examinations, including those with medical certificates. This rule overrides any faculty-specific leniency guidelines. Students falling below this threshold will receive an 'F' grade for the respective course due to attendance default.

## Section 4: Academic Integrity
Honesty is the foundation of the Medicaps academic philosophy. Plagiarism, cheating, unauthorized collaboration, and fabrication of data are strictly penalized. First offenses usually result in a zero grade for the assignment. Repeated offenses may lead to suspension or expulsion. The disciplinary committee evaluates all reported cases of academic misconduct. Students are required to submit their research through university-approved similarity checking software.

## Section 5: Grading System
The grading system uses a 4.0 scale. A (4.0) stands for excellent, B (3.0) for good, C (2.0) for satisfactory, D (1.0) for marginal, and F (0.0) for failure. An incomplete grade (I) is awarded only under severe extenuating circumstances and must be resolved within the first four weeks of the subsequent semester. Failure to resolve it results in an automatic F. The semester Grade Point Average (GPA) and Cumulative Grade Point Average (CGPA) are calculated based on credit hours and grade points.

## Section 6: Leave of Absence
A student may apply for a Leave of Absence for up to one academic year. Valid reasons include severe health issues, military service, or extreme financial hardship. The application must be filed prior to the midpoint of the semester. Retrospective leave is rarely granted.

## Section 7: Semester Fee Payments
Financial obligations must be settled promptly to ensure uninterrupted academic services. All semester fees must be remitted no later than July 15 for the Fall semester, and December 15 for the Spring semester. Failure to meet this exact deadline will result in immediate suspension of library privileges and portal access. No extensions are granted beyond July 15.

## Section 8: Graduation Requirements
To qualify for a Bachelor's degree, a student must complete a minimum of 120 credit hours with a CGPA not lower than 2.0. The capstone project must be passed. All university dues must be cleared, and all disciplinary sanctions resolved.

""" * 4

# -----------------
# 2. HOSTEL HANDBOOK (PDF)
# -----------------
HOSTEL_HANDBOOK_TEXT = """
# TITLE: Medicaps University Hostel Resident Handbook
## Section 1: Welcome and General Philosophy
Welcome to the Medicaps University residential community. The hostels are designed to provide a safe, inclusive, and conducive environment for study and personal growth. Living on campus is a privilege that comes with the responsibility of respecting community standards. 

## Section 2: Room Allocation and Maintenance
Rooms are allocated on a first-come, first-served basis, prioritizing out-of-state and international students. Residents are responsible for the cleanliness and upkeep of their assigned rooms. Any damage to university property will be billed to the resident's account. Routine maintenance checks happen monthly.

## Section 3: Hostel Curfew and Timing
Security is a paramount concern for the university. Therefore, strict timing regulations are enforced. Undergraduate hostel residents must return to the hostel by 10:00 PM. No entries are permitted after this time without prior written approval from the Chief Warden. 

## Section 4: Guest Policy
Guests of the same gender are allowed to visit rooms between 10:00 AM and 8:00 PM. Overnight guests are strictly prohibited. Non-resident students must sign the guest register at the security desk.

## Section 5: Disciplinary Actions in Hostels
Violation of hostel rules, including noise complaints, unauthorized guests, and possession of prohibited items (such as alcohol, illicit drugs, or unauthorized appliances) will lead to immediate disciplinary hearings.

## Section 6: Emergency Procedures
In case of a fire or medical emergency, residents must follow the evacuation maps posted on every floor. The assembly point is the central campus field. Fire drills are conducted unannounced twice a semester.

""" * 4

# -----------------
# 3. MEDICAL EXEMPTIONS (MD)
# -----------------
MEDICAL_EXEMPTIONS_MD = """# Medicaps University Medical Exemptions Policy

## Overview
This document outlines the standard operating procedures for granting medical exemptions to students taking courses at Medicaps University. The University recognizes that severe and unpredictable health crises can disrupt a student's educational trajectory. 

## Section 1: Application Process
Students seeking a medical exemption from academic obligations must submit their request via the university's health portal within 48 hours of the medical incident. The request must be supported by verifiable medical documentation. The University Health Center reserves the right to authenticate all external medical claims.

## Section 2: Attendance Threshold Alterations
The institution generally requires high attendance for all students. However, recognizing genuine health emergencies, special provisions are constructed. Students presenting a valid Type A Medical Certificate from the University Hospital are eligible to sit for examinations provided their overall attendance is at least 60%. This allowance is designed to accommodate prolonged hospitalizations or severe contagious phases.

## Section 3: Midterm and Final Exam Accommodations
If a student misses a midterm exam due to an approved medical emergency, the weight of the missed exam may be shifted to the final examination, or a make-up exam may be scheduled at the instructor's discretion. If a final exam is missed, the student receives an 'Incomplete' grade until a supplementary exam is arranged in the following semester.

## Section 4: Chronic Conditions
Students with documented chronic health conditions must register with the Office of Disability Services at the beginning of the academic year. Accommodations (e.g., extended testing time, alternative seating) are determined reasonably.

## Section 5: Psychological and Mental Health Leaves
Mental health is treated with the same severity as physical health. The University Counseling Center evaluates recommendations for course load reductions or leaves of absence due to mental health crises. 
""" * 4

# -----------------
# 4. STUDENT DISCIPLINE (MD)
# -----------------
STUDENT_DISCIPLINE_MD = """# Medicaps University Student Code of Conduct and Discipline

## Executive Summary
Medicaps University aims to maintain an environment where free speech, safety, and mutual respect thrive. This document specifies behavioral expectations.

## Part I: Campus Behavior
Students are expected to behave politely and professionally. Harassment, bullying, public intoxication, and physical altercations carry severe penalties, up to immediate expulsion.

## Part II: Curfew and Movement Regulations
While the campus promotes freedom of movement during standard hours, nocturnal restrictions are mandated by the city's ordinances and university security policy. Undergraduate hostel residents may remain outside the hostel until 11:00 PM on ordinary days. Security gates lock precisely at this hour.

## Part III: Dress Code
While the university generally respects individual expression, students must wear appropriate attire in laboratories, formal examinations, and official ceremonies. Laboratory safety requires closed-toe shoes and protective eyewear.

## Part IV: Social Media and Cyber Conduct
Cyberbullying, unauthorized distribution of class materials, and impersonating university officials on social media constitute severe misconduct.

## Part V: Disciplinary Board Procedures
When a violation is reported, an investigative officer gathers preliminary evidence. If the evidence has merit, the student is called before the Disciplinary Board, composed of faculty and student representatives. Decisions are delivered within standard business days.
""" * 4

# -----------------
# 5. EXAMINATION POLICY (MD)
# -----------------
EXAMINATION_POLICY_MD = """# Medicaps University Examination Procedures

## 1. General Directives
Examinations are the primary mode of summative assessment. The Office of the Registrar coordinates all centrally scheduled exams.

## 2. Invigilation and Exam Hall Rules
Students must arrive at the examination hall at least 15 minutes before the start time. No student will be admitted after the first 30 minutes. Students cannot leave the hall during the first hour. Electronic devices, smartwatches, and programmable calculators are forbidden unless expressly permitted.

## 3. Results Publication
Results for final examinations are typically processed and published on the student portal within three weeks of the examination period's conclusion. 

## 4. Re-evaluation and Appeals
If a student believes a grading error occurred, they may apply for a script re-evaluation. A non-refundable fee applies. The script will be marked by an independent faculty member, and the new score is final, whether higher or lower.

## 5. Alternative Assessments
Certain practical subjects may replace standard written examinations with portfolio submissions, viva voce, or extensive laboratory practicals.
""" * 4

# -----------------
# 6. SCHOLARSHIP POLICY (MD)
# -----------------
SCHOLARSHIP_POLICY_MD = """# Medicaps University Financial Aid and Scholarship Policy

## Merit-Based Scholarships
The university awards the President's Merit Scholarship to the top 2% of the incoming freshmen class. This covers 100% of tuition costs. Maintenance of this scholarship requires a minimum CGPA of 3.8 each semester.

## Need-Based Grants
The Opportunity Grant supports students demonstrating significant financial need. Applications must include verified tax returns and family income statements. Grants range from 20% to 50% tuition reduction.

## Athletic Scholarships
Students participating in varsity-level sports may qualify for athletic scholarships. Awardees must maintain a 2.5 CGPA and fulfill all team training obligations.

## Disqualification Criteria
Scholarships and grants are immediately revoked if a student is found guilty of major academic misconduct (e.g., plagiarism) or is suspended for disciplinary reasons. Re-application is not permitted in these scenarios. Payments made post-revocation must be refunded.
""" * 4


def generate_pdf(filename, text_content):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    style_n = styles['Normal']
    style_h = styles['Heading1']
    style_sh = styles['Heading2']
    
    story = []
    lines = text_content.split('\n')
    for line in lines:
        if line.startswith('# TITLE:') or line.startswith('# '):
            story.append(Paragraph(line.replace('# ', '').replace('TITLE: ', ''), style_h))
            story.append(Spacer(1, 12))
        elif line.startswith('## '):
            story.append(Paragraph(line.replace('## ', ''), style_sh))
            story.append(Spacer(1, 8))
        elif line.strip() == '':
            continue
        else:
            story.append(Paragraph(line.strip(), style_n))
            story.append(Spacer(1, 6))
            
    doc.build(story)

def create_fee_schedule_csv():
    rows = [
        ["Category", "Semester", "Program", "Deadline", "Amount"],
        ["Tuition Fee", "Fall", "Engineering", "July 31", "5000"],
        ["Tuition Fee", "Fall", "Arts", "July 31", "4000"],
        ["Tuition Fee", "Spring", "Engineering", "December 31", "5000"],
        ["Library Fee", "Annual", "All", "July 31", "200"],
        ["Laboratory Fee", "Fall", "Engineering", "July 31", "400"],
        ["Hostel Rent", "Fall", "All", "August 10", "1500"],
        ["Hostel Rent", "Spring", "All", "January 10", "1500"],
        ["Graduation Fee", "Final", "All", "May 1", "300"],
    ]
    with open(os.path.join(DATA_DIR, "fee_schedule.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        for i in range(20):
             for r in rows:
                 if r[0] == "Category":
                     if i == 0: writer.writerow(r)
                     continue
                 writer.writerow([r[0], r[1], r[2] + f" Variation {i}", r[3], r[4]])

def main():
    print("Generating Academic Regulations PDF...")
    generate_pdf(os.path.join(DATA_DIR, "academic_regulations.pdf"), ACADEMIC_REGULATIONS_TEXT)
    
    print("Generating Hostel Handbook PDF...")
    generate_pdf(os.path.join(DATA_DIR, "hostel_handbook.pdf"), HOSTEL_HANDBOOK_TEXT)
    
    with open(os.path.join(DATA_DIR, "medical_exemptions.md"), "w", encoding="utf-8") as f:
        f.write(MEDICAL_EXEMPTIONS_MD)
        
    with open(os.path.join(DATA_DIR, "student_discipline.md"), "w", encoding="utf-8") as f:
        f.write(STUDENT_DISCIPLINE_MD)
        
    with open(os.path.join(DATA_DIR, "examination_policy.md"), "w", encoding="utf-8") as f:
        f.write(EXAMINATION_POLICY_MD)

    with open(os.path.join(DATA_DIR, "scholarship_policy.md"), "w", encoding="utf-8") as f:
        f.write(SCHOLARSHIP_POLICY_MD)
        
    create_fee_schedule_csv()
    print("Generation Complete.")

if __name__ == "__main__":
    main()
