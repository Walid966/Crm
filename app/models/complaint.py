from app import db
from datetime import datetime

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_complaints_user_id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisors.id', name='fk_complaints_supervisor_id'), nullable=True)
    representative_id = db.Column(db.Integer, db.ForeignKey('representatives.id', name='fk_complaints_representative_id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', name='fk_complaints_service_id'), nullable=False)
    sub_service_id = db.Column(db.Integer, db.ForeignKey('sub_services.id', name='fk_complaints_sub_service_id'), nullable=False)
    merchant_account = db.Column(db.String(50), nullable=False)
    transaction_number = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    attachment = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, resolved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    responses = db.relationship('ComplaintResponse', backref='complaint', lazy=True, cascade='all, delete-orphan')
    supervisor = db.relationship('Supervisor', backref='complaints', lazy=True)
    representative = db.relationship('Representative', backref='complaints', lazy=True)
    service = db.relationship('Service', backref='complaints', lazy=True)
    sub_service = db.relationship('SubService', backref='complaints', lazy=True)
    
    def __repr__(self):
        return f'<Complaint {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'supervisor_id': self.supervisor_id,
            'representative_id': self.representative_id,
            'service_id': self.service_id,
            'sub_service_id': self.sub_service_id,
            'merchant_account': self.merchant_account,
            'transaction_number': self.transaction_number,
            'notes': self.notes,
            'attachment': self.attachment,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class ComplaintResponse(db.Model):
    __tablename__ = 'complaint_responses'
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id', name='fk_complaint_responses_complaint_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_complaint_responses_user_id'), nullable=False)
    response = db.Column(db.Text, nullable=False)
    attachment = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ComplaintResponse {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'user_id': self.user_id,
            'response': self.response,
            'attachment': self.attachment,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 