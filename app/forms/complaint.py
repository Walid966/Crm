from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FileField, DateField, SubmitField
from wtforms.validators import Optional, DataRequired, Length, Regexp
from flask_wtf.file import FileField
from app.models import Service, SubService
from flask import current_app

class ComplaintSearchForm(FlaskForm):
    supervisor_account = StringField('رقم حساب المشرف')
    user_account = StringField('رقم حساب المستخدم')
    merchant_account = StringField('رقم حساب التاجر')
    transaction_number = StringField('رقم العملية')
    service = SelectField('الخدمة', coerce=int, choices=[], validators=[Optional()])
    sub_service = SelectField('الخدمة الفرعية', coerce=int, choices=[], validators=[Optional()])
    status = SelectField('الحالة', choices=[
        ('', 'الكل'),
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'قيد المعالجة'),
        ('resolved', 'تم الحل'),
        ('rejected', 'مرفوضة')
    ], validators=[Optional()])
    date_from = DateField('من تاريخ', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateField('إلى تاريخ', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('بحث')

class ComplaintForm(FlaskForm):
    merchant_account = StringField('رقم حساب التاجر', validators=[
        DataRequired(message='يجب إدخال رقم حساب التاجر'),
        Regexp(r'^\d+$', message='يجب إدخال أرقام فقط')
    ])
    service = SelectField('الخدمة', coerce=int, validators=[
        DataRequired(message='يجب اختيار الخدمة')
    ])
    sub_service = SelectField('الخدمة الفرعية', coerce=int, validators=[
        DataRequired(message='يجب اختيار الخدمة الفرعية')
    ])
    transaction_number = StringField('رقم العملية', validators=[
        DataRequired(message='يجب إدخال رقم العملية'),
        Regexp(r'^\d+$', message='يجب إدخال أرقام فقط')
    ])
    notes = TextAreaField('ملاحظات', validators=[
        DataRequired(message='يجب إدخال ملاحظات'),
        Length(min=10, message='يجب أن تحتوي الملاحظات على 10 أحرف على الأقل')
    ])
    attachment = FileField('المرفقات', validators=[
        DataRequired(message='يجب إرفاق ملف مع الشكوى')
    ])
    submit = SubmitField('إرسال')

class ComplaintResponseForm(FlaskForm):
    response = TextAreaField('الرد', validators=[
        DataRequired(message='يجب إدخال الرد')
    ])
    status = SelectField('الحالة', choices=[
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'قيد المعالجة'),
        ('resolved', 'تم الحل'),
        ('rejected', 'مرفوضة')
    ])
    attachment = FileField('المرفقات')
    submit = SubmitField('إرسال')

    def __init__(self, *args, **kwargs):
        super(ComplaintResponseForm, self).__init__(*args, **kwargs)
        # إخفاء حقل الحالة لمستخدمي المبيعات
        from flask_login import current_user
        if current_user.role == 'sales':
            del self.status