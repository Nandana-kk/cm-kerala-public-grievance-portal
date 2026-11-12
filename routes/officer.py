"""
Department Officer Route Module for CM Kerala Grievance Redressal Portal.
Allows department officers to view assigned grievances, update investigation progress,
and submit Action Taken Reports (ATR). Enforces department-level data isolation.
"""

import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename
from database import query_db, execute_db
from routes.auth import login_required, role_required

officer_bp = Blueprint("officer", __name__, url_prefix="/officer")


def allowed_file(filename):
    """Check if uploaded file has an allowed extension."""
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "pdf", "doc", "docx"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@officer_bp.route("/dashboard")
@login_required
@role_required("officer")
def dashboard():
    """Department Officer dashboard displaying complaints assigned to their department only."""
    dept_id = session.get("department_id")
    if not dept_id:
        flash("You are not associated with any government department.", "danger")
        return redirect(url_for("auth.login"))

    # Fetch department info
    dept = query_db("SELECT department_name FROM departments WHERE department_id = %s", (dept_id,), one=True)
    dept_name = dept["department_name"] if dept else "Your Department"

    # Status filter
    status_filter = request.args.get("status", "").strip()
    search_query = request.args.get("search", "").strip()

    sql = """
        SELECT g.*, u.name AS citizen_name, u.mobile AS citizen_mobile
        FROM grievances g
        LEFT JOIN users u ON g.citizen_id = u.user_id
        WHERE g.assigned_department = %s
    """
    params = [dept_id]

    if status_filter:
        sql += " AND g.status = %s"
        params.append(status_filter)

    if search_query:
        sql += " AND (g.reference_number LIKE %s OR g.subject LIKE %s)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term])

    sql += " ORDER BY g.created_at DESC"
    grievances = query_db(sql, tuple(params))

    # Officer department metrics
    total_assigned = query_db(
        "SELECT COUNT(*) AS c FROM grievances WHERE assigned_department = %s",
        (dept_id,),
        one=True
    )["c"]

    in_progress = query_db(
        "SELECT COUNT(*) AS c FROM grievances WHERE assigned_department = %s AND status = 'In Progress'",
        (dept_id,),
        one=True
    )["c"]

    under_review = query_db(
        "SELECT COUNT(*) AS c FROM grievances WHERE assigned_department = %s AND status = 'Under Review'",
        (dept_id,),
        one=True
    )["c"]

    resolved = query_db(
        "SELECT COUNT(*) AS c FROM grievances WHERE assigned_department = %s AND status = 'Resolved'",
        (dept_id,),
        one=True
    )["c"]

    return render_template(
        "officer_dashboard.html",
        dept_name=dept_name,
        grievances=grievances,
        total_assigned=total_assigned,
        in_progress=in_progress,
        under_review=under_review,
        resolved=resolved,
        selected_status=status_filter,
        search_query=search_query
    )


@officer_bp.route("/grievance/<int:grievance_id>")
@login_required
@role_required("officer")
def grievance_details(grievance_id):
    """View details of a grievance assigned to the officer's department."""
    dept_id = session.get("department_id")

    # Strict departmental access control
    grievance = query_db(
        """
        SELECT g.*, d.department_name, u.name AS citizen_name, u.email AS citizen_email, u.mobile AS citizen_mobile
        FROM grievances g
        LEFT JOIN departments d ON g.assigned_department = d.department_id
        LEFT JOIN users u ON g.citizen_id = u.user_id
        WHERE g.grievance_id = %s
        """,
        (grievance_id,),
        one=True
    )

    if not grievance:
        flash("Grievance not found.", "danger")
        return redirect(url_for("officer.dashboard"))

    # Enforce isolation: Prevent officers from accessing other departments' grievances
    if grievance["assigned_department"] != dept_id:
        flash("Unauthorized access: This grievance is assigned to another department.", "danger")
        return redirect(url_for("officer.dashboard"))

    # Fetch status history
    history = query_db(
        """
        SELECT gh.*, u.name AS actor_name, u.role AS actor_role
        FROM grievance_history gh
        LEFT JOIN users u ON gh.changed_by = u.user_id
        WHERE gh.grievance_id = %s
        ORDER BY gh.changed_at ASC
        """,
        (grievance_id,)
    )

    # Fetch attachments
    attachments = query_db(
        "SELECT * FROM attachments WHERE grievance_id = %s",
        (grievance_id,)
    )

    return render_template(
        "grievance_details.html",
        grievance=grievance,
        history=history,
        attachments=attachments,
        is_officer_view=True
    )


@officer_bp.route("/grievance/<int:grievance_id>/submit-report", methods=["POST"])
@login_required
@role_required("officer")
def submit_action_taken_report(grievance_id):
    """Officer submits investigation remarks or Action Taken Report (ATR)."""
    dept_id = session.get("department_id")
    officer_id = session.get("user_id")

    # Verify grievance ownership
    grievance = query_db(
        "SELECT status, assigned_department FROM grievances WHERE grievance_id = %s",
        (grievance_id,),
        one=True
    )

    if not grievance or grievance["assigned_department"] != dept_id:
        flash("Unauthorized access: You cannot update complaints belonging to another department.", "danger")
        return redirect(url_for("officer.dashboard"))

    previous_status = grievance["status"]
    new_status = request.form.get("status")
    investigation_remarks = request.form.get("investigation_remarks", "").strip()
    action_taken_report = request.form.get("action_taken_report", "").strip()

    valid_statuses = ["Under Review", "In Progress", "Resolved"]
    if new_status not in valid_statuses:
        new_status = previous_status

    if not investigation_remarks and not action_taken_report:
        flash("Please provide investigation remarks or an action-taken report.", "danger")
        return redirect(url_for("officer.grievance_details", grievance_id=grievance_id))

    # Handle optional verification document upload
    file = request.files.get("report_attachment")
    if file and file.filename != "":
        if allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_file_name = f"officer_{timestamp_str}_{original_filename}"
            upload_folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_folder, exist_ok=True)
            full_save_path = os.path.join(upload_folder, saved_file_name)
            file.save(full_save_path)
            saved_file_path = f"uploads/{saved_file_name}"

            execute_db(
                "INSERT INTO attachments (grievance_id, file_name, file_path) VALUES (%s, %s, %s)",
                (grievance_id, saved_file_name, saved_file_path)
            )

    # Build updated ATR
    combined_report = action_taken_report if action_taken_report else investigation_remarks

    execute_db(
        """
        UPDATE grievances
        SET status = %s, action_taken_report = %s, updated_at = CURRENT_TIMESTAMP
        WHERE grievance_id = %s
        """,
        (new_status, combined_report, grievance_id)
    )

    # Log in grievance_history
    history_entry = f"Officer Update [{session.get('name', 'Officer')}]: {investigation_remarks}"
    if action_taken_report:
        history_entry += f" | Action Taken Report: {action_taken_report}"

    execute_db(
        """
        INSERT INTO grievance_history (grievance_id, previous_status, new_status, changed_by, remarks)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (grievance_id, previous_status, new_status, officer_id, history_entry)
    )

    flash("Investigation progress / Action Taken Report updated successfully.", "success")
    return redirect(url_for("officer.grievance_details", grievance_id=grievance_id))
