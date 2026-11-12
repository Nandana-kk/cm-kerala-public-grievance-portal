# 08. Required Project Diagrams

## CM KERALA – Chief Minister's Public Grievance Redressal Portal
**Assessment:** WhiteMatrix Software Solutions – AI Full Stack Engineer Machine Test  
**Prototype Year:** 2026  

This document consolidates all mandatory system and database architecture diagrams in standard Mermaid format for technical evaluation and interview presentation.

---

## 1. High-Level System Architecture Flowchart
Illustrates the 4-tier architecture comprising the Client Presentation Layer, Flask Application/Controller Layer, External AI & File Services, and the MySQL Database Tier.

```mermaid
flowchart TD
    %% CLIENT LAYER
    subgraph ClientLayer ["1. Presentation / Client Layer (Browser)"]
        direction TB
        Citizen["Citizen Interface\n(Registration, Submission, AI Pre-Check, Tracking, Feedback)"]
        Admin["CMO Admin Dashboard\n(Chart.js Analytics, Triage, Department Routing, Approval)"]
        Officer["Department Officer Dashboard\n(Isolated Dept Workflows, Investigation, ATR Submission)"]
        Public["Public Pages\n(Home, About Us, How It Works, Departments, FAQ, Contact)"]
    end

    %% PROTOCOL / GATEWAY
    ClientLayer <-->|HTTPS / HTTP REST Requests| AppGateway["Flask Web Application Gateway\n(app.py - Port 5000)"]

    %% APPLICATION / BUSINESS LOGIC LAYER
    subgraph BackendLayer ["2. Application & Controller Layer (Python Flask)"]
        direction TB
        AppGateway --> Security["Security & Session Middleware\n- Werkzeug PBKDF2 Password Hashing\n- Flask HTTP-Only Sessions\n- Role-Based Access Control (@role_required)"]
        
        Security --> AuthBP["auth.py\n(Register, Login, Session Management, Logout)"]
        Security --> CitizenBP["citizen.py\n(Submit Grievances, Generate Ref No, Track Lifecycle, Post Feedback)"]
        Security --> AdminBP["admin.py\n(Grievance Filtering, Dept/Officer Assignment, Priority Escalation, ATR Review)"]
        Security --> OfficerBP["officer.py\n(Department Data Isolation, Field Notes, Action Taken Report - ATR)"]
        Security --> AIBP["ai.py\n(Complaint Text Analysis, Category Triage, Priority Suggestion, Fallback)"]
    end

    %% EXTERNAL SERVICES & FILE STORAGE
    subgraph ServiceLayer ["3. External AI & File Storage Services"]
        direction TB
        GeminiAPI["Google Gemini API\n(Official SDK: google-genai / Model: gemini-2.5-flash)"]
        FileStorage["Local Uploads Storage\n(uploads/ - Photos, PDF, DOCX up to 10MB)"]
    end

    AIBP <-->|API Key in .env / JSON Prompt & Response| GeminiAPI
    CitizenBP & OfficerBP -->|Sanitized File I/O| FileStorage

    %% DATABASE ACCESS LAYER
    subgraph DatabaseLayer ["4. Database Tier (MySQL 8.0+ - cm_kerala_portal)"]
        direction TB
        DBHelper["database.py\n(mysql-connector-python with 100% Parameterized Queries)"]
        
        subgraph Tables ["Relational Tables & Foreign Key Constraints"]
            T_Users[("users\n(Roles: citizen, admin, officer)")]
            T_Depts[("departments\n(PWD, Health, Water, LSGD, KSEB, etc.)")]
            T_Griev[("grievances\n(Ref No, District, Status, Priority, AI Summary)")]
            T_Hist[("grievance_history\n(Audit Log: Previous & New Status, Actor, Remarks)")]
            T_Assign[("department_assignments\n(Grievance to Dept & Officer Mapping)")]
            T_Attach[("attachments\n(File Names & Document Paths)")]
            T_Feed[("feedback\n(1-5 Star Ratings & Comments)")]
            T_Contact[("contact_enquiries\n(Public Questions & Contact Messages)")]
        end
    end

    BackendLayer <--> DBHelper
    DBHelper <--> Tables

    %% STYLING
    classDef clientStyle fill:#e8f5e9,stroke:#0d5c3a,stroke-width:2px,color:#09472c;
    classDef backendStyle fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;
    classDef serviceStyle fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e;
    classDef dbStyle fill:#f1f5f9,stroke:#334155,stroke-width:2px,color:#0f172a;

    class Citizen,Admin,Officer,Public clientStyle;
    class Security,AuthBP,CitizenBP,AdminBP,OfficerBP,AIBP backendStyle;
    class GeminiAPI,FileStorage serviceStyle;
    class DBHelper,T_Users,T_Depts,T_Griev,T_Hist,T_Assign,T_Attach,T_Feed,T_Contact dbStyle;
```

---

## 2. Database Entity-Relationship (ER) Diagram
Defines the 8 relational tables in MySQL, their primary keys (PK), foreign keys (FK), unique constraints, and cardinalities.

```mermaid
erDiagram
    DEPARTMENTS ||--o{ USERS : "employs (officers)"
    DEPARTMENTS ||--o{ GRIEVANCES : "assigned_to"
    DEPARTMENTS ||--o{ DEPARTMENT_ASSIGNMENTS : "department_reference"
    
    USERS ||--o{ GRIEVANCES : "submits (citizen)"
    USERS ||--o{ GRIEVANCE_HISTORY : "actor (changed_by)"
    USERS ||--o{ DEPARTMENT_ASSIGNMENTS : "assigned_officer"
    USERS ||--o{ FEEDBACK : "submits_rating (citizen)"
    
    GRIEVANCES ||--o{ GRIEVANCE_HISTORY : "audit_log"
    GRIEVANCES ||--o{ DEPARTMENT_ASSIGNMENTS : "routing_history"
    GRIEVANCES ||--o{ ATTACHMENTS : "supporting_evidence"
    GRIEVANCES ||--o{ FEEDBACK : "citizen_review"

    USERS {
        int user_id PK
        varchar name
        varchar email UK
        varchar mobile
        varchar password_hash
        enum role "citizen, admin, officer"
        int department_id FK
        datetime created_at
    }

    DEPARTMENTS {
        int department_id PK
        varchar department_name UK
        text description
        datetime created_at
    }

    GRIEVANCES {
        int grievance_id PK
        varchar reference_number UK
        int citizen_id FK
        varchar district
        varchar category
        varchar subject
        text description
        enum priority "Low, Medium, High"
        enum status "Submitted, Under Review, In Progress, Resolved, Reopened"
        int assigned_department FK
        text ai_summary
        varchar ai_suggested_department
        varchar ai_suggested_category
        varchar ai_suggested_priority
        text cmo_remarks
        text action_taken_report
        datetime created_at
        datetime updated_at
    }

    GRIEVANCE_HISTORY {
        int history_id PK
        int grievance_id FK
        varchar previous_status
        varchar new_status
        int changed_by FK
        text remarks
        datetime changed_at
    }

    DEPARTMENT_ASSIGNMENTS {
        int assignment_id PK
        int grievance_id FK
        int department_id FK
        int officer_id FK
        datetime assigned_at
    }

    ATTACHMENTS {
        int attachment_id PK
        int grievance_id FK
        varchar file_name
        varchar file_path
        datetime uploaded_at
    }

    FEEDBACK {
        int feedback_id PK
        int grievance_id FK
        int citizen_id FK
        int rating "1 to 5"
        text comments
        datetime created_at
    }

    CONTACT_ENQUIRIES {
        int enquiry_id PK
        varchar name
        varchar email
        varchar subject
        text message
        datetime created_at
    }
```

---

## 3. End-to-End Grievance Workflow Sequence Diagram
Tracks the interaction across all actors and components from citizen complaint submission through AI triage, CMO administrative assignment, officer field work, resolution approval, and feedback.

```mermaid
sequenceDiagram
    autonumber
    actor Citizen
    participant Portal as Web Portal (Flask)
    participant AI as Google Gemini API
    participant DB as MySQL Database
    actor CMO as CMO Administrator
    actor Officer as Department Officer

    Citizen->>Portal: Enters grievance description & district
    Citizen->>Portal: Clicks "Analyze with Gemini AI"
    Portal->>AI: POST complaint text + active department list
    AI-->>Portal: Returns structured JSON {dept, category, priority, summary}
    Portal-->>Citizen: Renders AI recommendations in UI
    Citizen->>Portal: Submits Grievance + optional attachment
    Portal->>DB: INSERT into grievances (Status: Submitted)
    Portal->>DB: INSERT into grievance_history (Submitted)
    Portal-->>Citizen: Displays unique Reference No. (e.g., KL-2026-PWD-8401)

    CMO->>Portal: Logs in & views CMO Dashboard metrics
    CMO->>Portal: Reviews grievance & AI briefing
    CMO->>Portal: Forwards to Department (e.g. PWD) + adds remarks
    Portal->>DB: UPDATE status = 'Under Review', assigned_department
    Portal->>DB: INSERT into department_assignments & grievance_history

    Officer->>Portal: Logs in to Department Officer Dashboard
    Note over Officer,Portal: Department Isolation enforced by session['department_id']
    Officer->>Portal: Inspects assigned complaint & attachments
    Officer->>Portal: Sets status = 'In Progress' & enters field inspection notes
    Portal->>DB: UPDATE status = 'In Progress' & INSERT grievance_history

    Officer->>Portal: Submits Action Taken Report (ATR) + verification photo
    Portal->>DB: UPDATE action_taken_report & INSERT grievance_history

    CMO->>Portal: Audits Action Taken Report & photos
    CMO->>Portal: Approves resolution -> status = 'Resolved'
    Portal->>DB: UPDATE status = 'Resolved' & INSERT grievance_history

    Citizen->>Portal: Tracks Reference Number on public tracking page
    Citizen->>Portal: Submits 1-5 Star Satisfaction Rating & Comments
    Portal->>DB: INSERT into feedback
```

---

## 4. Grievance State Machine Diagram
Illustrates the exact 5 grievance statuses and allowable state transitions recorded in `grievance_history`.

```mermaid
stateDiagram-v2
    [*] --> Submitted : Citizen registers complaint online\n(Ref: KL-2026-XXX-XXXX)
    
    Submitted --> Under_Review : CMO reviews & assigns department
    Submitted --> In_Progress : Direct emergency field dispatch by CMO
    
    Under_Review --> In_Progress : Department officer initiates ground work
    Under_Review --> Resolved : Administrative direct resolution
    
    In_Progress --> Resolved : Officer submits Action Taken Report (ATR)\n& CMO approves resolution
    
    Resolved --> Reopened : Citizen disputes resolution\nor recurring ground failure flagged by CMO
    
    Reopened --> In_Progress : Officer re-investigates & undertakes corrective works
    Reopened --> Under_Review : CMO reassigns to alternate department
    
    Resolved --> [*] : Redressal verified & citizen submits feedback
```

---

## 5. AI Grievance Assistant Decision Flowchart
Shows how the asynchronous AI triage evaluates user inputs, validates them against MySQL departments, queries similar cases, calls Google Gemini, and falls back gracefully when needed.

```mermaid
flowchart TD
    Start["Citizen enters complaint description\n(Length >= 15 characters)"] --> Click["Citizen clicks 'Analyze with Gemini AI'"]
    Click --> AJAX["AJAX POST to /api/ai/analyze-grievance"]
    
    AJAX --> FetchDepts["Query active departments\nfrom MySQL departments table"]
    FetchDepts --> FetchSimilar["Query recent grievances in same district\n(Duplicate Detection)"]
    
    FetchSimilar --> CheckKey{"Is GEMINI_API_KEY\nconfigured in .env?"}
    
    CheckKey -- Yes --> CallGemini["Call Google GenAI SDK\nclient.models.generate_content\nModel: gemini-2.5-flash\nMIME: application/json"]
    
    CallGemini --> APISuccess{"API Call\nSuccessful?"}
    
    APISuccess -- Yes --> ReturnLive["Return JSON with:\n- suggested_department\n- suggested_category\n- priority\n- summary\n- reason\n- duplicate_warning\nTag: is_live_ai = True"]
    
    APISuccess -- No (Error/Quota) --> Fallback["Execute Deterministic Rule-Based Fallback\nTag: is_live_ai = False\n(Clearly Labeled with Disclaimer)"]
    
    CheckKey -- No --> Fallback
    
    ReturnLive --> RenderUI["Render interactive recommendation card in UI"]
    Fallback --> RenderUI
    
    RenderUI --> CitizenDecision{"Citizen clicks\n'Apply Suggestions'?"}
    CitizenDecision -- Yes --> AutoFill["Auto-fill category, priority & department in form"]
    CitizenDecision -- No --> Manual["Citizen keeps custom selections"]
    
    AutoFill --> Submit["Submit Grievance to CMO"]
    Manual --> Submit
```
