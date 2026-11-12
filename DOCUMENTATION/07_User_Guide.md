# 07. User & Operator Guide

## CM KERALA – Chief Minister's Public Grievance Redressal Portal

---

## 1. Demo Evaluation Accounts
The application comes pre-seeded with test accounts representing all portal roles. You can also use the **"Click to Auto-fill"** demo buttons on the login screen (`/login`) for instantaneous evaluation.

| Role | Name | Email | Password | Scope / Jurisdiction |
| :--- | :--- | :--- | :--- | :--- |
| **CMO Admin** | CMO Administrator | `admin@cmkerala.gov.in` | `Admin@123` | Full administrative oversight, all departments |
| **Officer (PWD)** | Er. Rajesh Kumar | `officer.pwd@kerala.gov.in` | `Officer@123` | Public Works Department (PWD) only |
| **Officer (Health)** | Dr. Ananya Nair | `officer.health@kerala.gov.in` | `Officer@123` | Health & Family Welfare Department only |
| **Officer (Water)** | Er. Thomas Mathew | `officer.water@kerala.gov.in` | `Officer@123` | Water Resources Department only |
| **Citizen 1** | Sujith Narayanan | `sujith.citizen@example.com` | `Citizen@123` | Submitting citizen, tracking, and feedback |
| **Citizen 2** | Meera Krishnan | `meera.citizen@example.com` | `Citizen@123` | Submitting citizen, tracking, and feedback |

---

## 2. Citizen User Guide

### 2.1 Registering an Account
1. Click **"Register"** in the top navigation bar.
2. Provide your full name, email address, 10-digit mobile number, and password (min 6 characters).
3. Click **"Complete Registration"** and proceed to the login page.

### 2.2 Submitting a Grievance with AI Assistance
1. Sign in to your citizen account and click **"Submit Grievance"**.
2. Select your Kerala District (e.g., *Ernakulam*) and Grievance Category.
3. Enter a clear Subject title and a detailed description of the problem.
4. Click **"Analyze with Gemini AI Assistant"**:
   - The AI inspects your text in real time.
   - It displays the suggested government department, recommended category, priority level, and an executive briefing.
   - Click **"Apply Suggestions to Form"** to auto-select the recommended department and priority.
5. (Optional) Attach a supporting photograph or document (PNG, JPG, PDF up to 10MB).
6. Click **"Submit Grievance"**.
7. Note down your generated **Unique Reference Number** (e.g., `KL-2026-PWD-8401`).

### 2.3 Tracking Grievance Progress
1. Click **"Track Grievance"** in the navigation bar.
2. Enter your Reference Number.
3. View the live status badge, assigned department, CMO directives, department Action Taken Report (ATR), and the full chronological history timeline.

### 2.4 Providing Feedback
1. When your grievance status reaches **Resolved**, a feedback rating section unlocks.
2. Select a star rating (1 to 5 Stars), enter your review comments, and click **"Submit Feedback"**.

---

## 3. CMO Administrator User Guide

### 3.1 Overview & Metrics
1. Log in with `admin@cmkerala.gov.in` / `Admin@123`.
2. The CMO overview dashboard displays:
   - Real-time counters: Total, Pending, Resolved, and Overdue complaints.
   - Interactive Chart.js graphs displaying status, district, and departmental distributions.

### 3.2 Filtering & Searching
- Filter grievances by District, Category, Priority, or Status.
- Search by Reference Number, citizen name, or keywords.

### 3.3 Triage & Department Assignment
1. Click **"Manage"** next to any grievance in the table.
2. Review citizen details, uploaded photos, and the **AI Triage Recommendation**.
3. Under **"Assign to Department"**:
   - Select the target department (e.g., *Public Works Department*).
   - Optionally select a specific officer.
   - Add internal administrative directives in the remarks box.
4. Click **"Forward Grievance & Direct Action"**. The status changes to **Under Review** and an audit entry is logged.

### 3.4 Reviewing Action Taken Reports & Resolution Approval
1. Once the department officer has submitted an Action Taken Report (ATR), inspect the report and verification documents.
2. Under **"Administrative Review & Status"**:
   - Select **Resolved** to approve the closure.
   - If work is incomplete, select **Reopened** or check **"Escalate Grievance (Sets Priority to HIGH)"**.
   - Enter closure or escalation notes.
3. Click **"Update Status & Save Audit Log"**.

---

## 4. Department Officer User Guide

### 4.1 Department Isolation
1. Log in as an officer (e.g., `officer.pwd@kerala.gov.in` / `Officer@123`).
2. The dashboard displays **only** complaints forwarded by the CMO to your department. You cannot view or modify complaints belonging to other departments.

### 4.2 Field Investigation & Action Taken Reports (ATR)
1. In your officer dashboard, click **"Inspect & Report"** on an assigned grievance.
2. Review the problem description, location landmarks, and citizen attachments.
3. Update the status:
   - When initiating inspection: Set status to **In Progress** and enter progress remarks.
   - When field work is finished: Set status to **Resolved**, provide a detailed **Action Taken Report (ATR)** describing the engineering or administrative solution, and upload verification photos.
4. Click **"Submit Progress / ATR to CMO"**.
5. The update is transmitted to the Chief Minister's Office for final audit and is immediately visible to the citizen on their tracking timeline.
