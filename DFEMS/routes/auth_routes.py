from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, bcrypt
from models.user_model import User

auth_bp = Blueprint("auth", __name__)

# Home route


# Register route
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_password,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("register.html")

# Login route
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("auth.dashboard"))

    return render_template("login.html")

# Dashboard
@auth_bp.route("/dashboard")
@login_required
def dashboard():

    from models.case_model import Case
    from models.evidence_model import Evidence

    total_cases = Case.query.count()
    open_cases = Case.query.filter_by(status="Open").count()
    closed_cases = Case.query.filter_by(status="Closed").count()
    total_evidence = Evidence.query.count()
    tampered_evidence = Evidence.query.filter_by(integrity_status="Tampered").count()

    return render_template(
        "dashboard.html",
        user=current_user,
        total_cases=total_cases,
        open_cases=open_cases,
        closed_cases=closed_cases,
        total_evidence=total_evidence,
        tampered_evidence=tampered_evidence
    )



# Logout
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
