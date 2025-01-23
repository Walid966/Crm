from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, FieldList, FormField, Form
from wtforms.validators import DataRequired, ValidationError
from app.models import Service, SubService, Supervisor, Representative

class RepresentativeEntryForm(Form):
    account_number = StringField('رقم الحساب', validators=[DataRequired(message='هذا الحقل مطلوب')])
    name = StringField('الاسم', validators=[DataRequired(message='هذا الحقل مطلوب')])

class SupervisorForm(FlaskForm):
    name = StringField('اسم المشرف', validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    account_number = StringField('رقم الحساب', validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    representatives = FieldList(FormField(RepresentativeEntryForm), min_entries=1)
    submit = SubmitField('حفظ')

    def validate_account_number(self, field):
        supervisor = Supervisor.query.filter_by(account_number=field.data).first()
        if supervisor and supervisor.id != getattr(self, 'id', None):
            raise ValidationError('رقم الحساب مستخدم بالفعل')

    def validate_representatives(self, field):
        account_numbers = []
        for entry in field.data:
            account_number = entry['account_number']
            if account_number in account_numbers:
                raise ValidationError('لا يمكن تكرار رقم حساب المندوب')
            account_numbers.append(account_number)
            
            representative = Representative.query.filter_by(account_number=account_number).first()
            if representative and representative.id != getattr(self, 'id', None):
                raise ValidationError(f'رقم حساب المندوب {account_number} مستخدم بالفعل')

class ServiceForm(FlaskForm):
    name = StringField('اسم الخدمة', validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    submit = SubmitField('حفظ')

    def validate_name(self, field):
        service = Service.query.filter_by(name=field.data).first()
        if service:
            raise ValidationError('نوع الخدمة موجود بالفعل')

class SubServiceForm(FlaskForm):
    service_id = SelectField('الخدمة', coerce=int, validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    name = StringField('اسم الخدمة الفرعية', validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    submit = SubmitField('حفظ')

    def validate_name(self, field):
        sub_service = SubService.query.filter_by(
            service_id=self.service_id.data,
            name=field.data
        ).first()
        if sub_service:
            raise ValidationError('الخدمة الفرعية موجودة بالفعل')

class RepresentativeForm(FlaskForm):
    name = StringField('اسم المندوب', validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    account_number = StringField('رقم الحساب', validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    supervisor_id = SelectField('المشرف', coerce=int, validators=[
        DataRequired(message='هذا الحقل مطلوب')
    ])
    submit = SubmitField('حفظ')

    def validate_account_number(self, field):
        representative = Representative.query.filter_by(account_number=field.data).first()
        if representative and representative.id != getattr(self, 'id', None):
            raise ValidationError('رقم الحساب مستخدم بالفعل') 