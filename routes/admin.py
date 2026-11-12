"""
CMO Administrator Route Module for CM Kerala Grievance Redressal Portal.
Handles administrative review, department/officer assignment, escalation,
action-taken report review, resolution approval, and Chart.js metrics.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import query_db, execute_db
from routes.auth import login_required, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    """CMO Administrator central overview dashboard."""
    # Filter parameters
    district_filter = request.args.get("district", "").strip()
    category_filter = request.args.get("category", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    status_filter = request.args.get("status", "").strip()
    search_query = request.args.get("search", "").strip()

    # Base query for grievance listing
    sql = """
        SELECT g.*, d.department_name, u.name AS citizen_name, u.mobile AS citizen_mobile
        FROM grievances g
        LEFT JOIN departments d ON g.assigned_department = d.department_id
        LEFT JOIN users u ON g.citizen_id = u.user_id
        WHERE 1=1
    """
    params = []

    if district_filter:
        sql += " AND g.district = %s"
        params.append(district_filter)
    if category_filter:
        sql += " AND g.category = %s"
        params.append(category_filter)
    if priority_filter:
        sql += " AND g.priority = %s"
        params.append(priority_filter)
    if status_filter:
        sql += " AND g.status = %s"
        params.append(status_filter)
    if search_query:
        sql += " AND (g.reference_number LIKE %s OR g.subject LIKE %s OR u.name LIKE %s)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term, like_term])

    sql += " ORDER BY g.created_at DESC"
    grievances = query_db(sql, tuple(params))

    # Overall Metrics from MySQL
    total_count = query_db("SELECT COUNT(*) AS c FROM grievances", one=True)["c"]
    resolved_count = query_db("SELECT COUNT(*) AS c FROM grievances WHERE status = 'Resolved'", one=True)["c"]
    pending_count = query_db("SELECT COUNT(*) AS c FROM grievances WHERE status IN ('Submitted', 'Under Review', 'In Progress', 'Reopened')", one=True)["c"]
    
    # Overdue count: unresolved grievances older than 7 days, or High priority older than 3 days
    overdue_count = query_db(
        """
        SELECT COUNT(*) AS c FROM grievances
        WHERE status != 'Resolved'
          AND (
            created_at < DATE_SUB(NOW(), INTERVAL 7 DAY)
            OR (priority = 'High' AND created_at < DATE_SUB(NOW(), INTERVAL 3 DAY))
          )
        """,
        one=True
    )["c"]

    # Filter lists
    districts = query_db("SELECT DISTINCT district FROM grievances WHERE district IS NOT NULL AND district != '' ORDER BY district")
    categories = query_db("SELECT DISTINCT category FROM grievances WHERE category IS NOT NULL AND category != '' ORDER BY category")
    departments = query_db("SELECT department_id, department_name FROM departments ORDER BY department_name")

    return render_template(
        "admin_dashboard.html",
        grievances=grievances,
        total_count=total_count,
        resolved_count=resolved_count,
        pending_count=pending_count,
        overdue_count=overdue_count,
        districts=[d["district"] for d in districts],
        categories=[c["category"] for c in categories],
        departments=departments,
        selected_district=district_filter,
        selected_category=category_filter,
        selected_priority=priority_filter,
        selected_status=status_filter,
        search_query=search_query
    )


@admin_bp.route("/api/chart-stats")
@login_required
@role_required("admin")
def chart_stats():
    """API endpoint providing real MySQL aggregation data for Chart.js."""
    # 1. Status Distribution
    status_rows = query_db(
        "SELECT status, COUNT(*) AS count FROM grievances GROUP BY status ORDER BY count DESC"
    )

    # 2. District-wise Complaints
    district_rows = query_db(
        "SELECT district, COUNT(*) AS count FROM grievances GROUP BY district ORDER BY count DESC LIMIT 8"
    )

    # 3. Department-wise Complaints
    dept_rows = query_db(
        """
        SELECT COALESCE(d.department_name, 'Unassigned') AS dept_name, COUNT(g.grievance_id) AS count
        FROM grievances g
        LEFT JOIN departments d ON g.assigned_department = d.department_id
        GROUP BY dept_name
        ORDER BY count DESC
        """
    )

    # 4. Priority Breakdown
    priority_rows = query_db(
        "SELECT priority, COUNT(*) AS count FROM grievances GROUP BY priority"
    )

    return jsonify({
        "status": {
            "labels": [r["status"] for r in status_rows],
            "data": [r["count"] for r in status_rows]
        },
        "districts": {
            "labels": [r["district"] for r in district_rows],
            "data": [r["count"] for r in district_rows]
        },
        "departments": {
            "labels": [r["dept_name"] for r in dept_rows],
            "data": [r["count"] for r in dept_rows]
        },
        "priorities": {
            "labels": [r["priority"] for r in priority_rows],
            "data": [r["count"] for r in priority_rows]
        }
    })


@admin_bp.route("/grievance/<int:grievance_id>")
@login_required
@role_required("admin")
def grievance_details(grievance_id):
    """View full grievance detail for CMO administration."""
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
        return redirect(url_for("admin.dashboard"))

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

    # Fetch feedback
    feedback = query_db(
        "SELECT * FROM feedback WHERE grievance_id = %s",
        (grievance_id,),
        one=True
    )

    # Fetch departments & officers for assignment dropdowns
    departments = query_db("SELECT department_id, department_name FROM departments ORDER BY department_name")
    
    # Officers for the currently assigned department (if any)
    officers = []
    if grievance["assigned_department"]:
        officers = query_db(
            "SELECT user_id, name, email FROM users WHERE role = 'officer' AND department_id = %s",
            (grievance["assigned_department"],)
        )

    # Current assignment record
    current_assignment = query_db(
        """
        SELECT da.*, u.name AS officer_name, u.email AS officer_email
        FROM department_assignments da
        LEFT JOIN users u ON da.officer_id = u.user_id
        WHERE da.grievance_id = %s
        ORDER BY da.assigned_at DESC
        LIMIT 1
        """,
        (grievance_id,),
        one=True
    )

    return render_template(
        "grievance_details.html",
        grievance=grievance,
        history=history,
        attachments=attachments,
        feedback=feedback,
        departments=departments,
        officers=officers,
        current_assignment=current_assignment
    )


@admin_bp.route("/grievance/<int:grievance_id>/assign", methods=["POST"])
@login_required
@role_required("admin")
def assign_department(grievance_id):
    """Assign or reassign a department and officer to a grievance."""
    admin_id = session["user_id"]
    department_id = request.form.get("department_id")
    officer_id = request.form.get("officer_id") or None
    cmo_remarks = request.form.get("cmo_remarks", "").strip()

    if not department_id:
        flash("Please select a valid department to assign.", "danger")
        return redirect(url_for("admin.grievance_details", grievance_id=grievance_id))

    grievance = query_db("SELECT status, assigned_department FROM grievances WHERE grievance_id = %s", (grievance_id,), one=True)
    if not grievance:
        flash("Grievance not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    previous_status = grievance["status"]
    new_status = "Under Review" if previous_status == "Submitted" else previous_status

    # Update grievance record
    execute_db(
        """
        UPDATE grievances
        SET assigned_department = %s, status = %s, cmo_remarks = %s, updated_at = CURRENT_TIMESTAMP
        WHERE grievance_id = %s
        """,
        (department_id, new_status, cmo_remarks or None, grievance_id)
    )

    # Create department assignment record
    execute_db(
        """
        INSERT INTO department_assignments (grievance_id, department_id, officer_id)
        VALUES (%s, %s, %s)
        """,
        (grievance_id, department_id, officer_id)
    )

    # Get department name for history log
    dept_info = query_db("SELECT department_name FROM departments WHERE department_id = %s", (department_id,), one=True)
    dept_name = dept_info["department_name"] if dept_info else f"Department #{department_id}"

    history_remarks = f"CMO forwarded grievance to {dept_name}."
    if cmo_remarks:
        history_remarks += f" Remarks: {cmo_remarks}"

    # Log transition in grievance_history
    execute_db(
        """
        INSERT INTO grievance_history (grievance_id, previous_status, new_status, changed_by, remarks)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (grievance_id, previous_status, new_status, admin_id, history_remarks)
    )

    flash(f"Grievance successfully assigned to {dept_name}.", "success")
    return redirect(url_for("admin.grievance_details", grievance_id=grievance_id))


@admin_bp.route("/grievance/<int:grievance_id>/update-status", methods=["POST"])
@login_required
@role_required("admin")
def update_status(grievance_id):
    """Update status, escalate, or add administrative remarks."""
    admin_id = session["user_id"]
    new_status = request.form.get("status")
    priority = request.form.get("priority")
    cmo_remarks = request.form.get("cmo_remarks", "").strip()
    is_escalation = request.form.get("is_escalation") == "true"

    valid_statuses = ["Submitted", "Under Review", "In Progress", "Resolved", "Reopened"]
    if new_status not in valid_statuses:
        flash("Invalid status specified.", "danger")
        return redirect(url_for("admin.grievance_details", grievance_id=grievance_id))

    grievance = query_db("SELECT status, priority FROM grievances WHERE grievance_id = %s", (grievance_id,), one=True)
    if not grievance:
        flash("Grievance not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    previous_status = grievance["status"]
    updated_priority = "High" if is_escalation else (priority or grievance["priority"])

    # Update grievance
    execute_db(
        """
        UPDATE grievances
        SET status = %s, priority = %s, cmo_remarks = %s, updated_at = CURRENT_TIMESTAMP
        WHERE grievance_id = %s
        """,
        (new_status, updated_priority, cmo_remarks or None, grievance_id)
    )

    remarks_text = cmo_remarks or f"Status updated to {new_status} by CMO Administrator."
    if is_escalation:
        remarks_text = f"[ESCALATED TO HIGH PRIORITY] {remarks_text}"

    # Log in grievance_history
    execute_db(
        """
        INSERT INTO grievance_history (grievance_id, previous_status, new_status, changed_by, remarks)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (grievance_id, previous_status, new_status, admin_id, remarks_text)
    )

    flash(f"Grievance status updated to '{new_status}'.", "success")
    return redirect(url_for("admin.grievance_details", grievance_id=grievance_id))
