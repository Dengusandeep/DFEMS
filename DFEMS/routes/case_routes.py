from models.custody_model import ChainOfCustody

import os
import time
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from flask_login import login_required, current_user
from extensions import db
from models.case_model import Case
from models.evidence_model import Evidence
from services.hash_service import generate_sha256

case_bp = Blueprint("case", __name__)

# ==============================
# Create Case
# ==============================
from sqlalchemy.exc import IntegrityError

@case_bp.route("/create_case", methods=["GET", "POST"])
@login_required
def create_case():
    if request.method == "POST":
        case_number = request.form["case_number"]
        title = request.form["title"]
        description = request.form["description"]

        new_case = Case(
            case_number=case_number,
            title=title,
            description=description,
            created_by=current_user.id
        )

        try:
            db.session.add(new_case)
            db.session.commit()
            return redirect(url_for("case.view_cases"))

        except IntegrityError:
            db.session.rollback()
            return render_template(
                "create_case.html",
                error="Case Number already exists!"
            )

    return render_template("create_case.html")


# ==============================
# View All Cases
# ==============================
@case_bp.route("/cases")
@login_required
def view_cases():
    cases = Case.query.all()
    return render_template("cases.html", cases=cases)


# ==============================
# Case Detail Page
# ==============================
@case_bp.route("/case/<int:case_id>")
@login_required
def case_detail(case_id):
    case = Case.query.get_or_404(case_id)
    evidence_list = Evidence.query.filter_by(case_id=case_id).all()

    return render_template(
        "case_detail.html",
        case=case,
        evidence_list=evidence_list
    )


# ==============================
# Upload Evidence
# ==============================
# ==============================
# Upload Evidence
# ==============================
@case_bp.route("/case/<int:case_id>/upload", methods=["POST"])
@login_required
def upload_evidence(case_id):

    case = Case.query.get_or_404(case_id)

    if case.status == "Closed":
     return "Case is closed. No further modifications allowed."


    files = request.files.getlist("file")

    for file in files:
        if file:
            filename = str(int(time.time())) + "_" + secure_filename(file.filename)

            upload_folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_folder, exist_ok=True)

            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            sha256_hash = generate_sha256(file_path)

            new_evidence = Evidence(
                case_id=case_id,
                file_name=filename,
                file_path=file_path,
                sha256_hash=sha256_hash,
                uploaded_by=current_user.id,
                integrity_status="Unknown"
            )

            # Step 1: Save evidence first
            db.session.add(new_evidence)
            db.session.commit()

            # Step 2: Log custody action
            custody_log = ChainOfCustody(
                evidence_id=new_evidence.id,
                action="Uploaded",
                performed_by=current_user.id
            )

            db.session.add(custody_log)
            db.session.commit()

    return redirect(url_for("case.case_detail", case_id=case_id))



# ==============================
# Evidence Detail Page
# ==============================
# Evidence Detail Page
@case_bp.route("/evidence/<int:evidence_id>")
@login_required
def evidence_detail(evidence_id):
    evidence = Evidence.query.get_or_404(evidence_id)

    custody_logs = ChainOfCustody.query.filter_by(
        evidence_id=evidence_id
    ).all()

    return render_template(
        "evidence_detail.html",
        evidence=evidence,
        custody_logs=custody_logs
    )




# ==============================
# Verify Integrity
# ==============================
# ==============================
# Verify Integrity
# ==============================
@case_bp.route("/evidence/<int:evidence_id>/verify")
@login_required
def verify_integrity(evidence_id):

    evidence = Evidence.query.get_or_404(evidence_id)

    current_hash = generate_sha256(evidence.file_path)

    if current_hash == evidence.sha256_hash:
        evidence.integrity_status = "Valid"
    else:
        evidence.integrity_status = "Tampered"

    # Log custody action
    custody_log = ChainOfCustody(
        evidence_id=evidence.id,
        action="Integrity Verified",
        performed_by=current_user.id
    )

    db.session.add(custody_log)
    db.session.commit()

    return redirect(url_for("case.evidence_detail", evidence_id=evidence_id))



# ==============================
# Download Evidence
# ==============================
from flask import send_from_directory

@case_bp.route("/evidence/<int:evidence_id>/download")
@login_required
def download_evidence(evidence_id):

    evidence = Evidence.query.get_or_404(evidence_id)

    # Log custody action
    custody_log = ChainOfCustody(
        evidence_id=evidence.id,
        action="Downloaded",
        performed_by=current_user.id
    )

    db.session.add(custody_log)
    db.session.commit()

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        evidence.file_name,
        as_attachment=True
    )




## ==============================
# Delete Evidence (Admin Only)
# ==============================
@case_bp.route("/evidence/<int:evidence_id>/delete")
@login_required
def delete_evidence(evidence_id):

    if current_user.role != "Admin":
        return "Access Denied"

    evidence = Evidence.query.get_or_404(evidence_id)

    # 🔒 Step 3 — Check if case is closed
    case = Case.query.get(evidence.case_id)

    if case.status == "Closed":
        return "Cannot delete evidence from a closed case."

    # Delete file from folder
    if os.path.exists(evidence.file_path):
        os.remove(evidence.file_path)

    # Log custody action
    custody_log = ChainOfCustody(
        evidence_id=evidence.id,
        action="Deleted",
        performed_by=current_user.id
    )

    db.session.add(custody_log)

    db.session.delete(evidence)
    db.session.commit()

    return redirect(url_for("case.case_detail", case_id=evidence.case_id))



# ==============================
# Edit Case
# ==============================
# ==============================
# Edit Case
# ==============================
@case_bp.route("/case/<int:case_id>/edit", methods=["GET", "POST"])
@login_required
def edit_case(case_id):

    case = Case.query.get_or_404(case_id)   # 🔹 First define case

    # 🔒 Lock if case closed
    if case.status == "Closed":
        return "Closed cases cannot be edited."

    if request.method == "POST":
        case.title = request.form["title"]
        case.description = request.form["description"]
        case.status = request.form["status"]

        db.session.commit()

        return redirect(url_for("case.case_detail", case_id=case_id))

    return render_template("edit_case.html", case=case)




# ==============================
# Delete Case (Admin Only)
# ==============================
@case_bp.route("/case/<int:case_id>/delete")
@login_required
def delete_case(case_id):

    if current_user.role != "Admin":
        return "Access Denied"

    case = Case.query.get_or_404(case_id)

    # Delete all evidence files
    evidences = Evidence.query.filter_by(case_id=case_id).all()

    for evidence in evidences:
        if os.path.exists(evidence.file_path):
            os.remove(evidence.file_path)

        db.session.delete(evidence)

    db.session.delete(case)
    db.session.commit()

    return redirect(url_for("case.view_cases"))



import zipfile
from io import BytesIO
from flask import send_file


# ==============================
# Download Full Case
# ==============================
@case_bp.route("/case/<int:case_id>/download")
@login_required
def download_full_case(case_id):

    case = Case.query.get_or_404(case_id)
    evidences = Evidence.query.filter_by(case_id=case_id).all()
    
    evidence_ids = [e.id for e in evidences]

    custody_logs = ChainOfCustody.query.filter(
    ChainOfCustody.evidence_id.in_(evidence_ids)
).all()

    memory_file = BytesIO()

    with zipfile.ZipFile(memory_file, 'w') as zf:

        # Add case details as text file
        case_info = f"""
Case Number: {case.case_number}
Title: {case.title}
Description: {case.description}
Status: {case.status}
Created At: {case.created_at}
"""

        zf.writestr("case_details.txt", case_info)

        # Add custody logs
        logs_text = ""
        for log in custody_logs:
            logs_text += f"{log.action} by User {log.performed_by} at {log.timestamp}\n"

        zf.writestr("chain_of_custody.txt", logs_text)

        # Add evidence files
        for evidence in evidences:
            if os.path.exists(evidence.file_path):
                zf.write(evidence.file_path, arcname=evidence.file_name)

    memory_file.seek(0)

    return send_file(
        memory_file,
        download_name=f"{case.case_number}_FULL_CASE.zip",
        as_attachment=True
    )





# ==============================
# Generate Professional PDF Case Report
# ==============================
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import TableStyle
from flask import send_file
import io


@case_bp.route("/case/<int:case_id>/report")
@login_required
def generate_case_report(case_id):

    case = Case.query.get_or_404(case_id)
    evidences = Evidence.query.filter_by(case_id=case_id).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("<b>DFEMS – Digital Forensics Case Report</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    # Case Info
    elements.append(Paragraph(f"<b>Case Number:</b> {case.case_number}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Title:</b> {case.title}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Description:</b> {case.description}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Status:</b> {case.status}", styles["Normal"]))
    elements.append(Spacer(1, 0.4 * inch))

    # Evidence Table
    data = [["File Name", "SHA256 Hash", "Integrity"]]

    for ev in evidences:
        data.append([
            ev.file_name,
            ev.sha256_hash,
            ev.integrity_status
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Case_{case.case_number}_Report.pdf",
        mimetype='application/pdf'
    )
