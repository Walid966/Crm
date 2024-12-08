from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional
from models import User, Supervisor, Representative
from flask_login import current_user

class LoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('هذا البريد الإلكتروني مستخدم بالفعل')

class ComplaintForm(FlaskForm):
    supervisor_account = SelectField('رقم حساب المشرف', validators=[DataRequired(message='يرجى اختيار المشرف')])
    representative_account = SelectField('رقم حساب المندوب', validators=[DataRequired(message='يرجى اختيار المندوب')])
    merchant_account = StringField('رقم حساب التاجر', validators=[DataRequired(message='يرجى إدخال رقم حساب التاجر')])
    service_type = SelectField('نوع الخدمة', validators=[DataRequired(message='يرجى اختيار نوع الخدمة')])
    sub_service = SelectField('الخدمة الفرعية', validators=[DataRequired(message='يرجى اختيار الخدمة الفرعية')])
    transaction_number = StringField('رقم العملية', validators=[DataRequired(message='يرجى إدخال رقم العملية')])
    notes = TextAreaField('ملاحظات')
    image = FileField('صورة الشكوى')

    def validate_merchant_account(self, field):
        if not field.data.isdigit():
            raise ValidationError('يجب أن يحتوي رقم حساب التاجر على أرقام فقط')

    def validate_transaction_number(self, field):
        if not field.data.isdigit():
            raise ValidationError('يجب أن يحتوي رقم العملية على أرقام فقط')

class SupervisorForm(FlaskForm):
    account_number = StringField('رقم حساب المشرف', validators=[DataRequired()])
    name = StringField('اسم المشرف', validators=[DataRequired()])

    def validate_account_number(self, field):
        if not field.data.isdigit():
            raise ValidationError('يجب أن يحتوي رقم الحساب على أرقام فقط')
        if Supervisor.query.filter_by(account_number=field.data).first():
            raise ValidationError('رقم الحساب مستخدم بالفعل')

class RepresentativeForm(FlaskForm):
    account_number = StringField('رقم حساب المندوب', validators=[DataRequired()])
    name = StringField('اسم المندوب', validators=[DataRequired()])

    def validate_account_number(self, field):
        if not field.data.isdigit():
            raise ValidationError('يجب أن يحتوي رقم الحساب على أرقام فقط')
        if Representative.query.filter_by(account_number=field.data).first():
            raise ValidationError('رقم الحساب مستخدم بالفعل')

class ServiceForm(FlaskForm):
    service_type = StringField('نوع الخدمة', validators=[DataRequired()])

class SubServiceForm(FlaskForm):
    name = StringField('اسم الخدمة الفرعية', validators=[DataRequired()])
    service_id = SelectField('نوع الخدمة', validators=[DataRequired()], coerce=int)

class ResponseForm(FlaskForm):
    response_text = TextAreaField('الرد', validators=[DataRequired()])

class ProfileForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[Optional(), Length(min=6)])
    current_password = PasswordField('كلمة المرور الحالية', validators=[DataRequired()])

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != current_user.id:
            raise ValidationError('هذا البريد الإلكتروني مستخدم بالفعل') 