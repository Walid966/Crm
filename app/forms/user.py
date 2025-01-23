from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp, Optional
from app.models import User

class UserForm(FlaskForm):
    account_number = StringField('رقم الحساب', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Regexp(r'^\d+$', message='يجب إدخال أرقام فقط')
    ])
    username = StringField('اسم المستخدم', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(min=3, max=80, message='يجب أن يكون اسم المستخدم بين 3 و 80 حرفاً')
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
        EqualTo('password', message='كلمة المرور غير متطابقة')
    ])
    supervisor_account = StringField('رقم حساب المشرف', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(max=20, message='يجب أن لا يتجاوز رقم حساب المشرف 20 رقماً')
    ])
    supervisor_name = StringField('اسم المشرف', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(max=64, message='يجب أن لا يتجاوز اسم المشرف 64 حرفاً')
    ])
    role = SelectField('الصلاحية', choices=[
        ('support', 'دعم فني'),
        ('sales', 'مبيعات')
    ], validators=[DataRequired(message='هذا الحقل مطلوب')])
    submit = SubmitField('حفظ')

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('اسم المستخدم مستخدم بالفعل')

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('البريد الإلكتروني مستخدم بالفعل')
            
    def validate_account_number(self, field):
        user = User.query.filter_by(account_number=field.data).first()
        if user:
            raise ValidationError('رقم الحساب مستخدم بالفعل')

class EditUserForm(FlaskForm):
    account_number = StringField('رقم الحساب', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Regexp(r'^\d+$', message='يجب إدخال أرقام فقط')
    ])
    username = StringField('اسم المستخدم', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(min=3, max=80, message='يجب أن يكون اسم المستخدم بين 3 و 80 حرفاً')
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    supervisor_account = StringField('رقم حساب المشرف', validators=[
        Optional(),
        Length(max=20, message='يجب أن لا يتجاوز رقم حساب المشرف 20 رقماً')
    ])
    supervisor_name = StringField('اسم المشرف', validators=[
        Optional(),
        Length(max=64, message='يجب أن لا يتجاوز اسم المشرف 64 حرفاً')
    ])
    role = SelectField('الصلاحية', choices=[
        ('support', 'دعم فني'),
        ('sales', 'مبيعات')
    ], validators=[DataRequired(message='هذا الحقل مطلوب')])
    submit = SubmitField('حفظ')

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user and user.username != field.data:
            raise ValidationError('اسم المستخدم مستخدم بالفعل')

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user and user.email != field.data:
            raise ValidationError('البريد الإلكتروني مستخدم بالفعل')

    def validate_account_number(self, field):
        user = User.query.filter_by(account_number=field.data).first()
        if user and user.account_number != field.data:
            raise ValidationError('رقم الحساب مستخدم بالفعل')

class ChangePasswordForm(FlaskForm):
    password = PasswordField('كلمة المرور الجديدة', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        Length(min=6, message='يجب أن تكون كلمة المرور 6 أحرف على الأقل')
    ])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[
        DataRequired(message='هذا الحقل مطلوب'),
        EqualTo('password', message='كلمة المرور غير متطابقة')
    ])
    submit = SubmitField('تغيير كلمة المرور')

class UserEditForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    account_number = StringField('رقم الحساب', validators=[DataRequired(), Length(min=1, max=20)])
    supervisor_account = StringField('رقم حساب المشرف', validators=[Optional(), Length(max=20)])
    supervisor_name = StringField('اسم المشرف', validators=[Optional(), Length(max=64)])
    role = SelectField('الصلاحية', choices=[('admin', 'مدير'), ('support', 'دعم فني'), ('sales', 'مبيعات')])
    submit = SubmitField('حفظ التغييرات') 