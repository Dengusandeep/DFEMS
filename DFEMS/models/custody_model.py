from extensions import db
from datetime import datetime

class ChainOfCustody(db.Model):
    __tablename__ = "chain_of_custody"

    id = db.Column(db.Integer, primary_key=True)
    evidence_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(100), nullable=False)
    performed_by = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
