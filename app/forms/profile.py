from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError, Regexp
from app.models import User

class ProfileForm(FlaskForm):
    account_number = StringField('رقم الحساب', validators=[
        DataRequired(message='رقم الحساب مطلوب'),
        Length(min=1, max=20, message='رقم الحساب يجب أن يكون بين 1 و 20 حرفاً')
    ])
    
    username = StringField('اسم المستخدم', validators=[
        DataRequired(message='اسم المستخدم مطلوب'),
        Length(min=3, max=64, message='اسم المستخدم يجب أن يكون بين 3 و 64 حرفاً')
    ])
    
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='البريد الإلكتروني مطلوب'),
        Email(message='البريد الإلكتروني غير صالح'),
        Length(max=120, message='البريد الإلكتروني يجب أن لا يتجاوز 120 حرفاً')
    ])
    
    current_password = PasswordField('كلمة المرور الحالية', validators=[
        Optional()
    ])
    
    new_password = PasswordField('كلمة المرور الجديدة', validators=[
        Optional(),
        Length(min=6, message='كلمة المرور يجب أن تكون 6 أحرف على الأقل')
    ])
    
    confirm_password = PasswordField('تأكيد كلمة المرور الجديدة', validators=[
        Optional(),
        EqualTo('new_password', message='كلمة المرور غير متطابقة')
    ])
    
    profile_image = FileField('الصورة الشخصية', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'يسمح فقط بالصور')
    ])
    
    submit = SubmitField('حفظ التغييرات')
    
    def __init__(self, original_username, original_email, original_account_number, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        self.original_account_number = original_account_number
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('اسم المستخدم مستخدم بالفعل')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('البريد الإلكتروني مستخدم بالفعل')
    
    def validate_account_number(self, account_number):
        if account_number.data != self.original_account_number:
            user = User.query.filter_by(account_number=account_number.data).first()
            if user:
                raise ValidationError('رقم الحساب مستخدم بالفعل') 