"""
Citizen Route Module for CM Kerala Grievance Redressal Portal.
Handles citizen dashboard, grievance submission, tracking, and feedback.
"""

import os
import random
import string
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, send_from_directory
from werkzeug.utils import secure_filename
from database import query_db, execute_db
from routes.auth import login_required, role_required

citizen_bp = Blueprint("citizen", __name__, url_prefix="/citizen")

# 14 Official Districts of Kerala
KERALA_DISTRICTS = [
    "Alappuzha",
    "Ernakulam",
    "Idukki",
    "Kannur",
    "Kasaragod",
    "Kollam",
    "Kottayam",
    "Kozhikode",
    "Malappuram",
    "Palakkad",
    "Pathanamthitta",
    "Thiruvananthapuram",
    "Thrissur",
    "Wayanad"
]

GRIEVANCE_CATEGORIES = [
    "Road Maintenance & Infrastructure",
    "Drinking Water Supply",
    "Healthcare Services & Hospitals",
    "Sanitation & Waste Management",
    "Electricity Supply & Power Grid",
    "Educational Institutions & Schools",
    "Land Records & Revenue Services",
    "Public Distribution & Ration Cards",
    "Public Transport & Traffic",
    "Disaster Relief & Flood Management",
    "Other Public Concerns"
]


def generate_unique_reference_number(department_code="GEN"):
    """Generate a unique Kerala government style reference number: KL-2026-XXX-XXXX"""
    year = datetime.now().year
    while True:
        random_digits = "".join(random.choices(string.digits, k=4))
        random_suffix = "".join(random.choices(string.ascii_uppercase, k=2))
        ref_no = f"KL-{year}-{department_code[:3].upper()}-{random_digits}{random_suffix}"
        existing = query_db("SELECT grievance_id FROM grievances WHERE reference_number = %s", (ref_no,), one=True)
        if not existing:
            return ref_no


def allowed_file(filename):
    """Check if uploaded file has an allowed extension."""
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "pdf", "doc", "docx"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@citizen_bp.route("/dashboard")
@login_required
@role_required("citizen")
def dashboard():
    """Citizen dashboard showing statistics and previous grievances."""
    citizen_id = session["user_id"]

    # Retrieve citizen's grievances
    grievances = query_db(
        """
        SELECT g.*, d.department_name
        FROM grievances g
        LEFT JOIN departments d ON g.assigned_department = d.department_id
        WHERE g.citizen_id = %s
        ORDER BY g.created_at DESC
        """,
        (citizen_id,)
    )

    total_count = len(grievances)
    resolved_count = sum(1 for g in grievances if g["status"] == "Resolved")
    pending_count = total_count - resolved_count
    in_progress_count = sum(1 for g in grievances if g["status"] == "In Progress")

    return render_template(
        "citizen_dashboard.html",
        grievances=grievances,
        total_count=total_count,
        resolved_count=resolved_count,
        pending_count=pending_count,
        in_progress_count=in_progress_count
    )


@citizen_bp.route("/submit", methods=["GET", "POST"])
@login_required
@role_required("citizen")
def submit_grievance():
    """Citizen grievance submission form."""
    departments = query_db("SELECT department_id, department_name FROM departments ORDER BY department_name")

    if request.method == "POST":
        district = request.form.get("district", "").strip()
        category = request.form.get("category", "").strip()
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        assigned_dept_id = request.form.get("department_id") or None

        # AI Recommendations captured from client
        ai_summary = request.form.get("ai_summary", "").strip()
        ai_dept = request.form.get("ai_suggested_department", "").strip()
        ai_cat = request.form.get("ai_suggested_category", "").strip()
        ai_pri = request.form.get("ai_suggested_priority", "").strip()

        errors = []

        if not district or district not in KERALA_DISTRICTS:
            errors.append("Please select a valid Kerala district.")

        if not category:
            errors.append("Please select a grievance category.")

        if not subject or len(subject) < 10:
            errors.append("Subject must be at least 10 characters long.")

        if not description or len(description) < 20:
            errors.append("Please provide a detailed description (minimum 20 characters).")

        if priority not in ["Low", "Medium", "High"]:
            priority = "Medium"

        # Handle optional file upload
        file = request.files.get("attachment")
        saved_file_name = None
        saved_file_path = None

        if file and file.filename != "":
            if not allowed_file(file.filename):
                errors.append("Invalid file format. Allowed formats: PNG, JPG, JPEG, PDF, DOC, DOCX.")
            else:
                original_filename = secure_filename(file.filename)
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                saved_file_name = f"{timestamp_str}_{original_filename}"
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                full_save_path = os.path.join(upload_folder, saved_file_name)
                file.save(full_save_path)
                saved_file_path = f"uploads/{saved_file_name}"

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "submit_grievance.html",
                districts=KERALA_DISTRICTS,
                categories=GRIEVANCE_CATEGORIES,
                departments=departments,
                district=district,
                category=category,
                subject=subject,
                description=description
            )

        # Generate unique reference number
        ref_number = generate_unique_reference_number()
        citizen_id = session["user_id"]

        try:
            # Insert grievance record into MySQL
            grievance_id = execute_db(
                """
                INSERT INTO grievances (
                    reference_number, citizen_id, district, category, subject, description,
                    priority, status, assigned_department, ai_summary, ai_suggested_department,
                    ai_suggested_category, ai_suggested_priority
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Submitted', %s, %s, %s, %s, %s)
                """,
                (
                    ref_number, citizen_id, district, category, subject, description,
                    priority, assigned_dept_id, ai_summary or None, ai_dept or None,
                    ai_cat or None, ai_pri or None
                ),
                return_id=True
            )

            # Insert initial grievance history entry
            execute_db(
                """
                INSERT INTO grievance_history (grievance_id, previous_status, new_status, changed_by, remarks)
                VALUES (%s, NULL, 'Submitted', %s, %s)
                """,
                (grievance_id, citizen_id, "Citizen submitted grievance online via Chief Minister's Portal.")
            )

            # Insert attachment if uploaded
            if saved_file_name:
                execute_db(
                    """
                    INSERT INTO attachments (grievance_id, file_name, file_path)
                    VALUES (%s, %s, %s)
                    """,
                    (grievance_id, saved_file_name, saved_file_path)
                )

            flash(
                f"Grievance submitted successfully! Your Reference Number is: {ref_number}. Keep this for tracking.",
                "success"
            )
            return redirect(url_for("citizen.track", ref=ref_number))

        except Exception as e:
            flash(f"Submission failed due to a database error: {e}", "danger")
            return render_template(
                "submit_grievance.html",
                districts=KERALA_DISTRICTS,
                categories=GRIEVANCE_CATEGORIES,
                departments=departments
            )

    return render_template(
        "submit_grievance.html",
        districts=KERALA_DISTRICTS,
        categories=GRIEVANCE_CATEGORIES,
        departments=departments
    )


@citizen_bp.route("/track")
def track():
    """Grievance tracking page. Accessible to public and logged-in citizens."""
    ref = request.args.get("ref", "").strip()
    status_filter = request.args.get("status", "").strip()
    grievance = None
    history = []
    attachments = []
    feedback = None

    if ref:
        grievance = query_db(
            """
            SELECT g.*, d.department_name, u.name AS citizen_name, u.mobile AS citizen_mobile, u.email AS citizen_email
            FROM grievances g
            LEFT JOIN departments d ON g.assigned_department = d.department_id
            LEFT JOIN users u ON g.citizen_id = u.user_id
            WHERE g.reference_number = %s
            """,
            (ref,),
            one=True
        )

        if grievance:
            # Fetch status history with actor names
            history = query_db(
                """
                SELECT gh.*, u.name AS actor_name, u.role AS actor_role
                FROM grievance_history gh
                LEFT JOIN users u ON gh.changed_by = u.user_id
                WHERE gh.grievance_id = %s
                ORDER BY gh.changed_at ASC
                """,
                (grievance["grievance_id"],)
            )

            # Fetch attachments
            attachments = query_db(
                "SELECT * FROM attachments WHERE grievance_id = %s",
                (grievance["grievance_id"],)
            )

            # Fetch existing feedback if any
            feedback = query_db(
                "SELECT * FROM feedback WHERE grievance_id = %s",
                (grievance["grievance_id"],),
                one=True
            )
        else:
            flash(f"No grievance found with Reference Number: '{ref}'. Please check and try again.", "warning")

    # Retrieve grievances list for the public table (filtered by status if requested)
    sql = """
        SELECT g.*, d.department_name, u.name AS citizen_name
        FROM grievances g
        LEFT JOIN departments d ON g.assigned_department = d.department_id
        LEFT JOIN users u ON g.citizen_id = u.user_id
        WHERE 1=1
    """
    params = []
    if status_filter and status_filter.lower() != "all":
        sql += " AND g.status = %s"
        params.append(status_filter)

    sql += " ORDER BY g.created_at DESC"
    grievances_list = query_db(sql, tuple(params))

    return render_template(
        "track_grievance.html",
        ref=ref,
        grievance=grievance,
        history=history,
        attachments=attachments,
        feedback=feedback,
        grievances=grievances_list,
        selected_status=status_filter
    )


@citizen_bp.route("/feedback/<int:grievance_id>", methods=["POST"])
@login_required
@role_required("citizen")
def submit_feedback(grievance_id):
    """Submit citizen rating and feedback for a resolved grievance."""
    citizen_id = session["user_id"]
    grievance = query_db(
        "SELECT * FROM grievances WHERE grievance_id = %s AND citizen_id = %s",
        (grievance_id, citizen_id),
        one=True
    )

    if not grievance:
        flash("Grievance not found or unauthorized.", "danger")
        return redirect(url_for("citizen.dashboard"))

    if grievance["status"] != "Resolved":
        flash("Feedback can only be submitted after the grievance is marked as Resolved.", "warning")
        return redirect(url_for("citizen.track", ref=grievance["reference_number"]))

    try:
        rating = int(request.form.get("rating", 5))
        if rating < 1 or rating > 5:
            rating = 5
    except ValueError:
        rating = 5

    comments = request.form.get("comments", "").strip()

    # Check if already submitted
    existing = query_db("SELECT feedback_id FROM feedback WHERE grievance_id = %s", (grievance_id,), one=True)
    if existing:
        execute_db(
            "UPDATE feedback SET rating = %s, comments = %s, created_at = CURRENT_TIMESTAMP WHERE grievance_id = %s",
            (rating, comments, grievance_id)
        )
        flash("Your feedback has been updated. Thank you!", "success")
    else:
        execute_db(
            "INSERT INTO feedback (grievance_id, citizen_id, rating, comments) VALUES (%s, %s, %s, %s)",
            (grievance_id, citizen_id, rating, comments)
        )
        flash("Thank you for your valuable feedback!", "success")

    return redirect(url_for("citizen.track", ref=grievance["reference_number"]))


@citizen_bp.route("/download/<filename>")
def download_file(filename):
    """Safely serve uploaded attachments."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename, as_attachment=False)
