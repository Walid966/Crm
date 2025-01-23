from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)  # جعل الحقل اختياريًا
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='sales')  # admin, support, sales
    profile_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    supervisor_account = db.Column(db.String(20))  # رقم حساب المشرف
    supervisor_name = db.Column(db.String(64))     # اسم المشرف
    
    # العلاقات
    complaints = db.relationship('Complaint', backref='user', lazy=True)
    responses = db.relationship('ComplaintResponse', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """تعيين كلمة المرور"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password, password)
    
    @property
    def unread_notifications_count(self):
        """عدد الإشعارات غير المقروءة"""
        from app.models import Notification
        return Notification.query.filter_by(user_id=self.id).count()
    
    @property
    def notifications_count(self):
        """إجمالي عدد الإشعارات"""
        from app.models import Notification
        return Notification.query.filter_by(user_id=self.id).count()
    
    @property
    def recent_notifications(self):
        """آخر 5 إشعارات"""
        from app.models import Notification
        return Notification.query.filter_by(user_id=self.id)\
            .order_by(Notification.created_at.desc())\
            .limit(5)\
            .all()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'profile_image': self.profile_image,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 