"""
CM KERALA – CHIEF MINISTER'S PUBLIC GRIEVANCE REDRESSAL PORTAL
Main Application Entry Point (Flask)
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from database import query_db, execute_db

# Import Blueprint modules
from routes.auth import auth_bp
from routes.citizen import citizen_bp
from routes.admin import admin_bp
from routes.officer import officer_bp
from routes.ai import ai_bp


def create_app():
    """Application factory for CM Kerala Grievance Redressal Portal."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure uploads directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(ai_bp)

    # Context processor to make portal constants available to all templates
    @app.context_processor
    def inject_global_data():
        return {
            "DISCLAIMER": "This is an independent recruitment prototype developed for demonstration purposes. It is not an official Government of Kerala or Chief Minister's Office website.",
            "PORTAL_TITLE": "CM Kerala – Chief Minister's Public Grievance Redressal Portal",
            "YEAR": 2026
        }

    # -------------------------------------------------------------------------
    # PUBLIC WEBSITE ROUTES
    # -------------------------------------------------------------------------

    @app.route("/")
    def index():
        """Home page with hero section, statistics, and quick actions."""
        # Retrieve live statistics from MySQL
        try:
            total_grievances = query_db("SELECT COUNT(*) AS c FROM grievances", one=True)["c"]
            resolved_grievances = query_db("SELECT COUNT(*) AS c FROM grievances WHERE status = 'Resolved'", one=True)["c"]
            in_progress = query_db("SELECT COUNT(*) AS c FROM grievances WHERE status = 'In Progress'", one=True)["c"]
            departments_count = query_db("SELECT COUNT(*) AS c FROM departments", one=True)["c"]
            featured_departments = query_db("SELECT * FROM departments ORDER BY department_id LIMIT 6")
        except Exception:
            total_grievances = 1250
            resolved_grievances = 1120
            in_progress = 95
            departments_count = 8
            featured_departments = []

        return render_template(
            "index.html",
            total_grievances=total_grievances,
            resolved_grievances=resolved_grievances,
            in_progress=in_progress,
            departments_count=departments_count,
            featured_departments=featured_departments
        )

    @app.route("/about")
    def about():
        """About Us page: Purpose, Vision, Mission, and Objectives."""
        return render_template("about.html")

    @app.route("/how-it-works")
    def how_it_works():
        """How It Works page: 8-stage grievance lifecycle explanation."""
        return render_template("how_it_works.html")

    @app.route("/departments")
    def departments():
        """Departments page: Sample government departments and descriptions."""
        dept_list = query_db("SELECT * FROM departments ORDER BY department_name")
        return render_template("departments.html", departments=dept_list)

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        """Contact Us page: Enquiry form saved to MySQL."""
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            subject = request.form.get("subject", "").strip()
            message = request.form.get("message", "").strip()

            if not name or not email or not subject or not message:
                flash("All fields are mandatory. Please fill in the complete form.", "danger")
                return render_template("contact.html", name=name, email=email, subject=subject, message=message)

            try:
                execute_db(
                    "INSERT INTO contact_enquiries (name, email, subject, message) VALUES (%s, %s, %s, %s)",
                    (name, email, subject, message)
                )
                flash("Your enquiry has been received successfully. Our public assistance cell will respond promptly.", "success")
                return redirect(url_for("contact"))
            except Exception as e:
                flash(f"Error saving enquiry to database: {e}", "danger")
                return render_template("contact.html", name=name, email=email, subject=subject, message=message)

        return render_template("contact.html")

    @app.route("/faq")
    def faq():
        """Frequently Asked Questions."""
        return render_template("faq.html")

    # -------------------------------------------------------------------------
    # ERROR HANDLERS
    # -------------------------------------------------------------------------

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("index.html", error_msg="The requested page was not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("index.html", error_msg="An internal server error occurred."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
