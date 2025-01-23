import os
import logging
from datetime import datetime
from flask import current_app, send_file, render_template
from werkzeug.utils import secure_filename
from PIL import Image

def setup_logging():
    """إعداد نظام التسجيل"""
    logging.basicConfig(
        format=current_app.config['LOG_FORMAT'],
        level=current_app.config['LOG_LEVEL'],
        handlers=[
            logging.FileHandler(current_app.config['LOG_FILE']),
            logging.StreamHandler()
        ]
    )

def allowed_file(filename):
    """التحقق من امتداد الملف"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_file(file, folder):
    """حفظ الملف المرفق"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
        
        # إذا كان الملف صورة، قم بضغطها
        if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            image = Image.open(file)
            image.thumbnail((800, 800))  # تغيير الحجم مع الحفاظ على النسبة
            image.save(filepath, optimize=True, quality=85)
        else:
            file.save(filepath)
        
        return os.path.join(folder, filename)
    return None

def delete_file(filepath):
    """حذف الملف"""
    if filepath:
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filepath)
        if os.path.exists(full_path):
            os.remove(full_path)

def format_datetime(dt):
    """تنسيق التاريخ والوقت"""
    if not dt:
        return ''
    return dt.strftime('%Y-%m-%d %H:%M')

def time_since(dt):
    """حساب الوقت المنقضي"""
    if not dt:
        return ''
    
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'الآن'
    
    minutes = seconds // 60
    if minutes < 60:
        return f'منذ {int(minutes)} دقيقة'
    
    hours = minutes // 60
    if hours < 24:
        return f'منذ {int(hours)} ساعة'
    
    days = hours // 24
    if days < 30:
        return f'منذ {int(days)} يوم'
    
    months = days // 30
    if months < 12:
        return f'منذ {int(months)} شهر'
    
    years = months // 12
    return f'منذ {int(years)} سنة'

def send_notification(user, title, message, link=None, notification_type='info'):
    """إرسال إشعار للمستخدم"""
    from app.models import Notification
    from app import db
    
    notification = Notification(
        user_id=user.id,
        title=title,
        message=message,
        link=link,
        type=notification_type
    )
    db.session.add(notification)
    db.session.commit()

def send_email(subject, recipient, template, **kwargs):
    """إرسال بريد إلكتروني"""
    from flask_mail import Message
    from app import mail
    
    msg = Message(
        subject=subject,
        recipients=[recipient],
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    msg.html = render_template(template, **kwargs)
    mail.send(msg)

def generate_excel(data, headers):
    """إنشاء ملف Excel"""
    import xlsxwriter
    from io import BytesIO
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    
    # تنسيق العناوين
    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#4B5563',
        'font_color': 'white'
    })
    
    # كتابة العناوين
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # كتابة البيانات
    for row, record in enumerate(data, start=1):
        for col, value in enumerate(record):
            worksheet.write(row, col, value)
    
    workbook.close()
    output.seek(0)
    return output

def generate_pdf(html):
    """إنشاء ملف PDF"""
    from weasyprint import HTML
    from io import BytesIO
    
    output = BytesIO()
    HTML(string=html).write_pdf(output)
    output.seek(0)
    return output 