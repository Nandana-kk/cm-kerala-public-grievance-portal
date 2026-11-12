"""
Database Seeding Script for CM Kerala Grievance Redressal Portal.
Creates demo accounts (Admin, Officers, Citizens), sample grievances across all 5 statuses,
status histories, and sample feedback.
"""

import sys
from pathlib import Path
from werkzeug.security import generate_password_hash

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database import init_db, execute_db, query_db


def seed():
    print("[Seeding] Initializing database tables...")
    init_db()

    print("[Seeding] Creating demo users...")

    # Passwords hashed with Werkzeug
    admin_pw = generate_password_hash("Admin@123")
    officer_pw = generate_password_hash("Officer@123")
    citizen_pw = generate_password_hash("Citizen@123")

    users_data = [
        # Admin (CMO)
        (
            "CMO Administrator",
            "admin@cmkerala.gov.in",
            "9447000001",
            admin_pw,
            "admin",
            None
        ),
        # Officer 1: PWD
        (
            "Er. Rajesh Kumar (PWD Officer)",
            "officer.pwd@kerala.gov.in",
            "9447000002",
            officer_pw,
            "officer",
            1
        ),
        # Officer 2: Health
        (
            "Dr. Ananya Nair (Health Officer)",
            "officer.health@kerala.gov.in",
            "9447000003",
            officer_pw,
            "officer",
            2
        ),
        # Officer 3: Water Resources
        (
            "Er. Thomas Mathew (Water Officer)",
            "officer.water@kerala.gov.in",
            "9447000004",
            officer_pw,
            "officer",
            5
        ),
        # Citizen 1
        (
            "Sujith Narayanan",
            "sujith.citizen@example.com",
            "9847012345",
            citizen_pw,
            "citizen",
            None
        ),
        # Citizen 2
        (
            "Meera Krishnan",
            "meera.citizen@example.com",
            "9847098765",
            citizen_pw,
            "citizen",
            None
        ),
    ]

    for name, email, mobile, pw_hash, role, dept_id in users_data:
        existing = query_db("SELECT user_id FROM users WHERE email = %s", (email,), one=True)
        if not existing:
            execute_db(
                """
                INSERT INTO users (name, email, mobile, password_hash, role, department_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (name, email, mobile, pw_hash, role, dept_id)
            )

    # Fetch user IDs for foreign key linkages
    admin_user = query_db("SELECT user_id FROM users WHERE email = 'admin@cmkerala.gov.in'", one=True)
    pwd_officer = query_db("SELECT user_id FROM users WHERE email = 'officer.pwd@kerala.gov.in'", one=True)
    health_officer = query_db("SELECT user_id FROM users WHERE email = 'officer.health@kerala.gov.in'", one=True)
    water_officer = query_db("SELECT user_id FROM users WHERE email = 'officer.water@kerala.gov.in'", one=True)
    citizen1 = query_db("SELECT user_id FROM users WHERE email = 'sujith.citizen@example.com'", one=True)
    citizen2 = query_db("SELECT user_id FROM users WHERE email = 'meera.citizen@example.com'", one=True)

    print("[Seeding] Creating sample grievances across all 5 statuses...")

    sample_grievances = [
        {
            "ref": "KL-2026-PWD-8401",
            "citizen_id": citizen1["user_id"],
            "district": "Ernakulam",
            "category": "Road Maintenance",
            "subject": "Deep dangerous potholes on Aluva-Perumbavoor road near bridge",
            "desc": "Multiple deep potholes have developed on the Aluva-Perumbavoor stretch causing traffic gridlock and two-wheeler accidents during evening peak hours. Immediate resurfacing required.",
            "priority": "High",
            "status": "Submitted",
            "dept_id": 1,
            "ai_summary": "Urgent pothole repairs required on critical commuter corridor in Aluva-Perumbavoor route.",
            "ai_dept": "Public Works Department (PWD)",
            "ai_cat": "Road Maintenance",
            "ai_pri": "High",
            "cmo_remarks": None,
            "atr": None,
            "history": [
                ("Submitted", None, citizen1["user_id"], "Citizen submitted grievance online.")
            ]
        },
        {
            "ref": "KL-2026-HLT-9122",
            "citizen_id": citizen2["user_id"],
            "district": "Thiruvananthapuram",
            "category": "Healthcare Services",
            "subject": "Shortage of essential pediatric and insulin medicines at Taluk Hospital",
            "desc": "Patients visiting the community health clinic and taluk pharmacy have been unable to obtain basic insulin and pediatric fever medicines for the past two weeks.",
            "priority": "Medium",
            "status": "Under Review",
            "dept_id": 2,
            "ai_summary": "Pharmacy stockout of insulin and pediatric supplies at Taluk Hospital, Thiruvananthapuram.",
            "ai_dept": "Health & Family Welfare Department",
            "ai_cat": "Healthcare Services",
            "ai_pri": "High",
            "cmo_remarks": "Forwarded to District Medical Officer for prompt medicine stock audit and replenishment.",
            "atr": None,
            "history": [
                ("Submitted", None, citizen2["user_id"], "Citizen submitted grievance."),
                ("Under Review", "Submitted", admin_user["user_id"], "CMO reviewing complaint details and assessing priority.")
            ]
        },
        {
            "ref": "KL-2026-WTR-3345",
            "citizen_id": citizen1["user_id"],
            "district": "Kozhikode",
            "category": "Drinking Water",
            "subject": "Main pipeline rupture resulting in clean drinking water wastage and road waterlogging",
            "desc": "A major Kerala Water Authority transmission line has ruptured near Mavoor road junction. Potable drinking water is gushing into the market area, causing low water pressure in 400 households.",
            "priority": "High",
            "status": "In Progress",
            "dept_id": 5,
            "ai_summary": "Severe potable water pipeline leakage affecting 400 households on Mavoor road.",
            "ai_dept": "Water Resources Department",
            "ai_cat": "Drinking Water",
            "ai_pri": "High",
            "cmo_remarks": "High priority incident. KWA engineering wing dispatched.",
            "atr": "KWA technical team has excavated the site, isolated the leaking valve section, and replacement pipe segments have arrived on site for jointing.",
            "history": [
                ("Submitted", None, citizen1["user_id"], "Grievance lodged."),
                ("Under Review", "Submitted", admin_user["user_id"], "CMO prioritized as High and assigned to Water Resources Dept."),
                ("In Progress", "Under Review", water_officer["user_id"], "Field inspection conducted. Repair crew actively working on pipe replacement.")
            ]
        },
        {
            "ref": "KL-2026-LSG-6789",
            "citizen_id": citizen2["user_id"],
            "district": "Thrissur",
            "category": "Sanitation & Waste Management",
            "subject": "Illegal roadside garbage dumping near Thrissur Round educational zone",
            "desc": "Large volumes of commercial plastic and organic waste were dumped along the sidewalk near the municipal high school, creating an unhygienic environment and stray dog menace.",
            "priority": "Medium",
            "status": "Resolved",
            "dept_id": 4,
            "ai_summary": "Sanitation and waste clearing required near municipal school zone.",
            "ai_dept": "Local Self Government Department (LSGD)",
            "ai_cat": "Sanitation & Waste Management",
            "ai_pri": "Medium",
            "cmo_remarks": "Approved closure after verifying clean-up report and geo-tagged photographs.",
            "atr": "Thrissur Municipal Corporation sanitation squad completely cleared the illegal dump site, sanitized the perimeter with bleaching powder, and installed CCTV surveillance warning signs.",
            "history": [
                ("Submitted", None, citizen2["user_id"], "Grievance registered."),
                ("Under Review", "Submitted", admin_user["user_id"], "CMO forwarded to LSGD Urban Sanitation Wing."),
                ("In Progress", "Under Review", admin_user["user_id"], "Sanitation squad deployed to clean site."),
                ("Resolved", "In Progress", admin_user["user_id"], "Action Taken Report verified and approved by CMO.")
            ]
        },
        {
            "ref": "KL-2026-ELC-4450",
            "citizen_id": citizen1["user_id"],
            "district": "Palakkad",
            "category": "Electricity Supply",
            "subject": "Recurring low voltage and agricultural feeder line tripping in Chittur",
            "desc": "Farmers in Chittur block face severe unannounced voltage drops daily from 10 AM to 4 PM, causing several agricultural water pump motors to burn out. Initial repair failed to stabilize voltage.",
            "priority": "Medium",
            "status": "Reopened",
            "dept_id": 6,
            "ai_summary": "Agricultural feeder low voltage causing equipment failure in Chittur.",
            "ai_dept": "Electricity Department (KSEB)",
            "ai_cat": "Electricity Supply",
            "ai_pri": "Medium",
            "cmo_remarks": "Reopened upon citizen dispute. KSEB Chief Engineer instructed to conduct transformer load balancing.",
            "atr": "Previous fuse replacement was temporary. Detailed assessment indicates a 100kVA transformer upgrade is necessary.",
            "history": [
                ("Submitted", None, citizen1["user_id"], "Grievance submitted."),
                ("Under Review", "Submitted", admin_user["user_id"], "CMO sent to KSEB Electrical Division."),
                ("In Progress", "Under Review", admin_user["user_id"], "Technicians tested local distribution feeder."),
                ("Resolved", "In Progress", admin_user["user_id"], "Reported resolved after fuse change."),
                ("Reopened", "Resolved", admin_user["user_id"], "Citizen reported voltage still below 170V. Reopened by CMO for transformer upgrade.")
            ]
        }
    ]

    for g in sample_grievances:
        existing_g = query_db("SELECT grievance_id FROM grievances WHERE reference_number = %s", (g["ref"],), one=True)
        if not existing_g:
            g_id = execute_db(
                """
                INSERT INTO grievances (
                    reference_number, citizen_id, district, category, subject, description,
                    priority, status, assigned_department, ai_summary, ai_suggested_department,
                    ai_suggested_category, ai_suggested_priority, cmo_remarks, action_taken_report
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    g["ref"], g["citizen_id"], g["district"], g["category"], g["subject"], g["desc"],
                    g["priority"], g["status"], g["dept_id"], g["ai_summary"], g["ai_dept"],
                    g["ai_cat"], g["ai_pri"], g["cmo_remarks"], g["atr"]
                ),
                return_id=True
            )

            # Insert history logs
            for new_st, prev_st, changed_by_id, rem in g["history"]:
                execute_db(
                    """
                    INSERT INTO grievance_history (grievance_id, previous_status, new_status, changed_by, remarks)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (g_id, prev_st, new_st, changed_by_id, rem)
                )

            # Department assignment record
            assigned_officer_id = None
            if g["dept_id"] == 1:
                assigned_officer_id = pwd_officer["user_id"]
            elif g["dept_id"] == 2:
                assigned_officer_id = health_officer["user_id"]
            elif g["dept_id"] == 5:
                assigned_officer_id = water_officer["user_id"]

            execute_db(
                """
                INSERT INTO department_assignments (grievance_id, department_id, officer_id)
                VALUES (%s, %s, %s)
                """,
                (g_id, g["dept_id"], assigned_officer_id)
            )

            # If resolved, add sample feedback
            if g["status"] == "Resolved":
                execute_db(
                    """
                    INSERT INTO feedback (grievance_id, citizen_id, rating, comments)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (g_id, g["citizen_id"], 5, "Prompt and effective resolution. Sidewalk was completely cleared within 48 hours. Thank you!")
                )

    # Add sample contact enquiry
    existing_enq = query_db("SELECT enquiry_id FROM contact_enquiries WHERE email = 'info.citizen@example.com'", one=True)
    if not existing_enq:
        execute_db(
            """
            INSERT INTO contact_enquiries (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
            """,
            (
                "Kavitha Varma",
                "info.citizen@example.com",
                "Query regarding tracking timeline",
                "Can we track grievances submitted through Akshaya centers using the same web portal reference number?"
            )
        )

    print("[Seeding Complete] Demo users, departments, grievances (all 5 statuses), history, and feedback seeded successfully!")


if __name__ == "__main__":
    seed()
