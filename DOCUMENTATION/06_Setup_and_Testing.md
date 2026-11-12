# 06. Setup and Testing Guide

## CM KERALA – Chief Minister's Public Grievance Redressal Portal

---

## 1. System Requirements
- **Operating System:** Windows, Linux, or macOS
- **Python:** Version 3.10+ (Tested on Python 3.14)
- **Database:** MySQL Server 8.0 or MariaDB 10.5+
- **Internet Connection:** Required for Google Gemini API inference and CDN assets (Bootstrap, Chart.js)

---

## 2. Installation & Environment Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/cm-kerala-portal.git
cd cm-kerala-portal
```

### Step 2: Create a Virtual Environment (Recommended)
```bash
# On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 3. Database Configuration

### Step 1: Configure `.env`
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to match your local MySQL server credentials:
```ini
SECRET_KEY=your-random-secret-key-for-session-encryption
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=cm_kerala_portal

# Google Gemini API Key (Get free key from https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### Step 2: Initialize & Seed the Database
Run the seed script to create all tables and populate demo accounts and sample complaints:
```bash
python scripts/seed_database.py
```
*Expected Output:*
```text
[Seeding] Initializing database tables...
[Database Initialization] All tables created and initial data seeded successfully.
[Seeding] Creating demo users...
[Seeding] Creating sample grievances across all 5 statuses...
[Seeding Complete] Demo users, departments, grievances (all 5 statuses), history, and feedback seeded successfully!
```

---

## 4. Running the Application

### Development Server:
```bash
python app.py
```
Open your browser and navigate to:  
**`http://127.0.0.1:5000`**

### Production WSGI Server:
```bash
# Linux / macOS (using Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

# Windows (using Waitress)
waitress-serve --port=5000 --call "app:create_app"
```

---

## 5. Automated Test Suite Execution
The repository includes a comprehensive automated test suite verifying all 13 recruitment assessment workflows and security isolation rules:
```bash
python tests/test_workflow.py -v
```

### Verified Test Cases:
| Test ID | Test Description | Verification Criteria | Status |
| :--- | :--- | :--- | :---: |
| **TEST 1** | Citizen Registration & Login | Input validation, duplicate rejection, Werkzeug hashing, session issuance | **PASS** |
| **TEST 2** | Citizen Grievance Submission | 14 districts, categories, file upload, status set to `Submitted` | **PASS** |
| **TEST 3** | Gemini AI Grievance Analysis | JSON response, department suggestion, priority assessment, summary | **PASS** |
| **TEST 4** | Unique Reference Number Generation | Generates format `KL-2026-XXX-XXXX` with database uniqueness | **PASS** |
| **TEST 5** | CMO Administrator Review | Overview counters, filterable listing, details view | **PASS** |
| **TEST 6** | Department & Officer Assignment | Routes to department, status transitions to `Under Review` | **PASS** |
| **TEST 7** | Department Officer Dashboard | Isolated dashboard displaying only grievances belonging to officer's dept | **PASS** |
| **TEST 8** | Officer Status & Investigation Update | Status changes to `In Progress`, inspection remarks recorded in history | **PASS** |
| **TEST 9** | Action Taken Report (ATR) Submission | Officer submits physical report + verification document attachment | **PASS** |
| **TEST 10** | CMO Resolution Approval | CMO verifies report and approves resolution (`status = 'Resolved'`) | **PASS** |
| **TEST 11** | Public Tracking & History Timeline | Search by reference number displays complete chronological history | **PASS** |
| **TEST 12** | Citizen Feedback & Rating | 1 to 5 star rating and review comments saved to `feedback` | **PASS** |
| **TEST 13** | Contact Enquiry Ingestion | General public enquiries saved to `contact_enquiries` table | **PASS** |
| **SECURITY** | Departmental Access Isolation | Prevents Officer from Dept A accessing or modifying Dept B's records | **PASS** |
| **CHART** | Real-Time MySQL Aggregations | `/admin/api/chart-stats` outputs real MySQL grouped aggregates | **PASS** |
