from extensions import db
from datetime import datetime

class Evidence(db.Model):
    __tablename__ = "evidence"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    sha256_hash = db.Column(db.String(64), nullable=False)
    uploaded_by = db.Column(db.Integer, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    integrity_status = db.Column(db.String(20), default="Unknown")
