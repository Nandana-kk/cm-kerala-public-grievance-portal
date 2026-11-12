"""
Authentication Route Module for CM Kerala Grievance Redressal Portal.
Handles citizen registration, login, logout, and role-based access control.
"""

import re
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import query_db, execute_db

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    """Decorator to protect routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this portal page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """Decorator to enforce specific roles (citizen, admin, officer)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for("auth.login", next=request.path))
            
            user_role = session.get("role")
            if user_role not in allowed_roles:
                flash("Access denied: You do not have authorization to view this dashboard.", "danger")
                if user_role == "admin":
                    return redirect(url_for("admin.dashboard"))
                elif user_role == "officer":
                    return redirect(url_for("officer.dashboard"))
                else:
                    return redirect(url_for("citizen.dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Citizen registration route."""
    if "user_id" in session:
        return redirect(url_for("citizen.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []

        # Server-side validation
        if not name or len(name) < 3:
            errors.append("Please provide a valid full name (minimum 3 characters).")
        
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not email or not re.match(email_regex, email):
            errors.append("Please provide a valid email address.")

        if not mobile or not re.match(r"^[0-9]{10}$", mobile):
            errors.append("Please provide a valid 10-digit Indian mobile number.")

        if len(password) < 6:
            errors.append("Password must be at least 6 characters long.")

        if password != confirm_password:
            errors.append("Password and Confirm Password do not match.")

        # Check for existing email in MySQL
        existing_user = query_db("SELECT user_id FROM users WHERE email = %s", (email,), one=True)
        if existing_user:
            errors.append("An account with this email address already exists. Please log in.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("register.html", name=name, email=email, mobile=mobile)

        # Hash password and insert into users table
        hashed_password = generate_password_hash(password)
        try:
            execute_db(
                """
                INSERT INTO users (name, email, mobile, password_hash, role)
                VALUES (%s, %s, %s, %s, 'citizen')
                """,
                (name, email, mobile, hashed_password)
            )
            flash("Registration successful! You may now log in with your credentials.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"Registration failed due to a database error: {e}", "danger")
            return render_template("register.html", name=name, email=email, mobile=mobile)

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Universal login route for Citizens, CMO Admins, and Department Officers."""
    if "user_id" in session:
        user_role = session.get("role")
        if user_role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif user_role == "officer":
            return redirect(url_for("officer.dashboard"))
        else:
            return redirect(url_for("citizen.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html", email=email)

        # Query user record from MySQL
        user = query_db(
            """
            SELECT u.user_id, u.name, u.email, u.mobile, u.password_hash, u.role, u.department_id,
                   d.department_name
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.department_id
            WHERE u.email = %s
            """,
            (email,),
            one=True
        )

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email address or password. Please try again.", "danger")
            return render_template("login.html", email=email)

        # Set user session
        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        session["email"] = user["email"]
        session["role"] = user["role"]
        session["department_id"] = user["department_id"]
        session["department_name"] = user.get("department_name")

        flash(f"Welcome back, {user['name']}!", "success")

        # Redirect based on role
        if user["role"] == "admin":
            return redirect(url_for("admin.dashboard"))
        elif user["role"] == "officer":
            return redirect(url_for("officer.dashboard"))
        else:
            return redirect(url_for("citizen.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Clear session and log out the user."""
    user_name = session.get("name", "User")
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("auth.login"))
