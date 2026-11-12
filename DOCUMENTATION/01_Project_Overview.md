# 01. Project Overview

## CM KERALA – Chief Minister's Public Grievance Redressal Portal
**Recruitment Machine Test Assignment – AI Full Stack Engineer**  
**Organization:** WhiteMatrix Software Solutions  
**Prototype Year:** 2026  

---

## 1. Problem Statement
In public administration, citizens frequently encounter civic, infrastructural, healthcare, educational, and service issues. Traditional administrative pathways suffer from significant pain points:
- **Bureaucratic fragmentation:** Citizens often do not know which specific department or executive authority possesses jurisdiction over a particular problem.
- **Opacity and lack of tracking:** Once a complaint is lodged, citizens have no visibility into who is examining the matter, field inspection progress, or expected completion timelines.
- **Delayed triage:** Administrative offices receive thousands of heterogeneous complaints without automated categorization, leading to severe backlogs.
- **Absence of accountability & feedback:** Action taken on the ground is rarely audited, and citizens cannot officially rate service delivery or dispute unsatisfactory closures.

---

## 2. Project Objectives
The objective of this project is to develop a functional, production-ready, and transparent web portal that establishes a direct digital bridge between the citizens of Kerala and the Chief Minister's Office (CMO):
1. **Single-Window Public Ingestion:** Allow citizens from all 14 districts of Kerala to submit grievances across multiple sectors (roads, water, electricity, healthcare, sanitation, schools, and land records).
2. **Transparent Reference Tracking:** Automatically generate a tamper-evident, unique grievance tracking number (`KL-2026-XXX-XXXX`) allowing real-time, public inspection without requiring recurring logins.
3. **AI-Powered Triage & Classification:** Integrate Google Gemini AI (`gemini-2.5-flash`) via the official Google GenAI Python SDK to automatically analyze complaint text, suggest the competent government department, determine category, assess priority level (Low/Medium/High), and generate an executive summary for the CMO.
4. **Hierarchical Multi-Role Workflow:** Implement role-based access for Citizens, CMO Administrators, and Department Officers, strictly enforcing departmental isolation so officers only access their own department's complaints.
5. **Verifiable Audit Trail:** Log every status transition permanently into a `grievance_history` table in MySQL, capturing actor, role, timestamp, previous status, new status, and remarks.
6. **Citizen Feedback Loop:** Enable citizens to rate resolved grievances from 1 to 5 stars and submit comments to evaluate administrative quality.

---

## 3. Project Scope
The portal encompasses:
- **Public Portal:** Home page with live MySQL statistics, About Us, How It Works (8-stage lifecycle), Participating Departments, Contact Enquiry form (saved to MySQL), and Frequently Asked Questions (FAQ).
- **Citizen Portal:** User registration with password hashing, secure session login, grievance submission with AI triage suggestions, file upload handling (photos/documents up to 10MB), citizen dashboard with status breakdown, and public reference number tracking.
- **CMO Administrative Dashboard:** Central administrative module displaying real-time metrics (Total, Pending, Resolved, Overdue), interactive Chart.js visualizations (Status Doughnut, District Bar, Department Bar), multi-attribute filtering (district, category, priority, status, keyword), department routing, officer assignment, priority escalation, and resolution verification.
- **Department Officer Dashboard:** Isolated workspace for department engineers and officers displaying only grievances forwarded to their specific department, field notes updating, and Action Taken Report (ATR) submission with verification document attachments.

---

## 4. Key Functional Features Summary

| Feature Area | Implementation Highlights |
| :--- | :--- |
| **Authentication & Security** | Werkzeug PBKDF2 password hashing, Flask session management, role-based route decorators (`@login_required`, `@role_required`). |
| **Database Architecture** | Direct MySQL queries using `mysql-connector-python` with 100% parameterized queries; 8 relational tables with foreign keys and cascading integrity. |
| **Grievance Lifecycle** | Exact 5-status workflow: `Submitted` &rarr; `Under Review` &rarr; `In Progress` &rarr; `Resolved` &rarr; `Reopened`. |
| **AI Integration** | Official Google GenAI Python SDK (`google-genai`), model `gemini-2.5-flash`, structured JSON responses, pre-submission suggestion, and clear fallback mechanism. |
| **Visual Analytics** | Chart.js interactive charts powered by live MySQL aggregations (`/admin/api/chart-stats`). |
| **File Handling** | Secure file upload validation (`.png`, `.jpg`, `.jpeg`, `.pdf`, `.doc`, `.docx`), 10 MB size limit, secure filename sanitization. |

---

## 5. Prototype Disclaimer
> **Mandatory Disclaimer:**  
> *"This is an independent recruitment prototype developed for demonstration purposes. It is not an official Government of Kerala or Chief Minister's Office website."*
