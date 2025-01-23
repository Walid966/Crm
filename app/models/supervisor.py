from app import db
from datetime import datetime

class Supervisor(db.Model):
    __tablename__ = 'supervisors'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, nullable=True)  # جعل الحقل اختياري
    username = db.Column(db.String(100), nullable=True)  # جعل الحقل اختياري
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    representatives = db.relationship('Representative', backref='supervisor', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Supervisor {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_number': self.account_number,
            'name': self.name,
            'user_id': self.user_id,
            'username': self.username,
            'representatives': [rep.to_dict() for rep in self.representatives],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Representative(db.Model):
    __tablename__ = 'representatives'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisors.id', name='fk_representatives_supervisor_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, nullable=True)  # جعل الحقل اختياري
    username = db.Column(db.String(100), nullable=True)  # جعل الحقل اختياري
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Representative {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_number': self.account_number,
            'name': self.name,
            'supervisor_id': self.supervisor_id,
            'user_id': self.user_id,
            'username': self.username,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
