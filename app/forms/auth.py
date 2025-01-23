from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from app.models import User

class LoginForm(FlaskForm):
    account_number = StringField('رقم الحساب', validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class RegisterForm(FlaskForm):
    account_number = StringField('رقم الحساب', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Regexp(r'^\d+$', message='يجب إدخال أرقام فقط')
    ])
    username = StringField('اسم المستخدم', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(min=3, max=80, message='يجب أن يكون اسم المستخدم بين 3 و 80 حرفاً'),
        Regexp(r'^[\u0600-\u06FFa-zA-Z0-9_]+$', message='يجب أن يحتوي اسم المستخدم على حروف عربية أو إنجليزية أو أرقام فقط')
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(min=6, message='يجب أن تكون كلمة المرور 6 أحرف على الأقل')
    ])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        EqualTo('password', message='كلمات المرور غير متطابقة')
    ])
    submit = SubmitField('تسجيل')

    def validate_account_number(self, field):
        user = User.query.filter_by(account_number=field.data).first()
        if user:
            raise ValidationError('رقم الحساب مستخدم بالفعل')

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('اسم المستخدم مستخدم بالفعل')

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('البريد الإلكتروني مستخدم بالفعل') 