# 04. API Documentation

## CM KERALA – Chief Minister's Public Grievance Redressal Portal

---

## 1. Overview
The portal exposes both web routes (rendering HTML interfaces) and REST API service endpoints for AJAX-based AI triage and dashboard visualization. All API endpoints use proper HTTP methods, standard HTTP status codes, and JSON response formats.

---

## 2. Authentication Endpoints

### 2.1 Citizen Registration
- **URL:** `/register`
- **Method:** `POST`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Parameters:**
  - `name` (string, required): Full name
  - `email` (string, required): Valid unique email address
  - `mobile` (string, required): 10-digit mobile number
  - `password` (string, required): Minimum 6 characters
  - `confirm_password` (string, required): Must match password
- **Response:**
  - `302 Redirect` to `/login` with success flash message.
  - `200 OK` with validation errors on invalid input.

### 2.2 Portal Login
- **URL:** `/login`
- **Method:** `POST`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Parameters:**
  - `email` (string, required): Account email
  - `password` (string, required): Password
- **Response:**
  - `302 Redirect` to role-specific dashboard (`/admin/dashboard`, `/officer/dashboard`, or `/citizen/dashboard`).
  - `401 / 200` with error flash message on invalid credentials.

### 2.3 Logout
- **URL:** `/logout`
- **Method:** `GET`
- **Response:**
  - `302 Redirect` to `/login` with session terminated.

---

## 3. Grievance Management Endpoints

### 3.1 Submit Grievance
- **URL:** `/citizen/submit`
- **Method:** `POST`
- **Authentication:** Required (Role: `citizen`)
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `district` (string, required): Kerala district
  - `category` (string, required): Grievance category
  - `subject` (string, required): Complaint title (min 10 chars)
  - `description` (string, required): Full complaint narrative (min 20 chars)
  - `priority` (string, optional): `Low`, `Medium`, or `High`
  - `department_id` (integer, optional): Preferred department ID
  - `attachment` (file, optional): Supporting file (`.jpg`, `.png`, `.pdf`, `.docx`)
  - `ai_summary` (string, optional): Generated AI summary
  - `ai_suggested_department` (string, optional): AI recommendation
  - `ai_suggested_category` (string, optional): AI category
  - `ai_suggested_priority` (string, optional): AI priority
- **Response:**
  - `302 Redirect` to `/citizen/track?ref=KL-2026-XXX-XXXX` with confirmation message.

### 3.2 Track Grievance by Reference Number
- **URL:** `/citizen/track`
- **Method:** `GET`
- **Authentication:** Public (No login required)
- **Query Parameter:** `ref` (string, required, e.g. `KL-2026-PWD-8401`)
- **Response:** `200 OK` (Renders timeline, assigned department, CMO remarks, and ATR).

### 3.3 Submit Citizen Feedback
- **URL:** `/citizen/feedback/<int:grievance_id>`
- **Method:** `POST`
- **Authentication:** Required (Role: `citizen`, must own grievance)
- **Parameters:**
  - `rating` (integer, required): Satisfaction rating between 1 and 5
  - `comments` (string, optional): Review text
- **Response:** `302 Redirect` to tracking view with updated feedback.

---

## 4. Administrative & Departmental Endpoints

### 4.1 Forward & Assign Grievance (CMO)
- **URL:** `/admin/grievance/<int:grievance_id>/assign`
- **Method:** `POST`
- **Authentication:** Required (Role: `admin`)
- **Parameters:**
  - `department_id` (integer, required): Target department
  - `officer_id` (integer, optional): Specific officer ID
  - `cmo_remarks` (string, optional): Directives from CMO
- **Response:** `302 Redirect` to grievance detail with success flash.

### 4.2 Administrative Status & Priority Update (CMO)
- **URL:** `/admin/grievance/<int:grievance_id>/update-status`
- **Method:** `POST`
- **Authentication:** Required (Role: `admin`)
- **Parameters:**
  - `status` (string, required): `Submitted` | `Under Review` | `In Progress` | `Resolved` | `Reopened`
  - `priority` (string, optional): `Low` | `Medium` | `High`
  - `cmo_remarks` (string, optional): Audit / closure notes
  - `is_escalation` (string, optional): `'true'` to force HIGH priority
- **Response:** `302 Redirect` with updated status recorded in `grievance_history`.

### 4.3 Submit Action Taken Report (Department Officer)
- **URL:** `/officer/grievance/<int:grievance_id>/submit-report`
- **Method:** `POST`
- **Authentication:** Required (Role: `officer`, must belong to assigned department)
- **Parameters:**
  - `status` (string, required): `In Progress` | `Resolved`
  - `investigation_remarks` (string, optional): Field inspection remarks
  - `action_taken_report` (string, optional): Comprehensive remedial report
  - `report_attachment` (file, optional): Verification photo / report
- **Response:** `302 Redirect` with updated ATR recorded in `grievances` and `grievance_history`.

---

## 5. REST & Chart API Endpoints

### 5.1 AI Grievance Assistant Endpoint
- **URL:** `/api/ai/analyze-grievance`
- **Method:** `POST`
- **Content-Type:** `application/json`
- **Request Body Example:**
```json
{
  "district": "Ernakulam",
  "description": "The main Aluva-Perumbavoor road has deep potholes near the bridge causing multiple accidents."
}
```
- **Response Example (Live Gemini API):**
```json
{
  "success": true,
  "is_live_ai": true,
  "ai_source": "Google Gemini API (gemini-2.5-flash)",
  "analysis": {
    "suggested_department": "Public Works Department (PWD)",
    "suggested_category": "Road Maintenance & Infrastructure",
    "priority": "High",
    "summary": "Severe pothole hazards on critical commuter route between Aluva and Perumbavoor causing traffic hazards.",
    "reason": "Road resurfacing and structural repairs fall under the administrative jurisdiction of the Public Works Department.",
    "possible_duplicate_warning": null
  }
}
```

### 5.2 CMO Chart.js Statistics Endpoint
- **URL:** `/admin/api/chart-stats`
- **Method:** `GET`
- **Authentication:** Required (Role: `admin`)
- **Response Example:**
```json
{
  "status": {
    "labels": ["Submitted", "Under Review", "In Progress", "Resolved", "Reopened"],
    "data": [2, 1, 1, 1, 1]
  },
  "districts": {
    "labels": ["Ernakulam", "Thiruvananthapuram", "Kozhikode", "Thrissur", "Palakkad"],
    "data": [2, 1, 1, 1, 1]
  },
  "departments": {
    "labels": ["Public Works Department (PWD)", "Water Resources Department", "Health & Family Welfare Department"],
    "data": [2, 1, 1]
  },
  "priorities": {
    "labels": ["High", "Medium", "Low"],
    "data": [3, 3, 0]
  }
}
```

### 5.3 Public Contact Enquiry Endpoint
- **URL:** `/contact`
- **Method:** `POST`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Parameters:** `name`, `email`, `subject`, `message`
- **Response:** `302 Redirect` to `/contact` with confirmation flash; record inserted into `contact_enquiries`.
