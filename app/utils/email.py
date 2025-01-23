from flask import current_app
from flask_mail import Message
from app import mail
from threading import Thread

def send_async_email(app, msg):
    """
    إرسال البريد الإلكتروني بشكل غير متزامن
    
    :param app: تطبيق Flask
    :param msg: رسالة البريد
    """
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, body, html=None, attachments=None):
    """
    إرسال بريد إلكتروني
    
    :param subject: عنوان الرسالة
    :param recipients: قائمة المستلمين
    :param body: نص الرسالة
    :param html: نص HTML للرسالة (اختياري)
    :param attachments: قائمة المرفقات (اختياري)
    :return: True إذا تم الإرسال بنجاح
    """
    try:
        msg = Message(subject,
                     sender=current_app.config['MAIL_DEFAULT_SENDER'],
                     recipients=recipients)
        msg.body = body
        
        if html:
            msg.html = html
        
        if attachments:
            for attachment in attachments:
                msg.attach(*attachment)
        
        Thread(target=send_async_email,
               args=(current_app._get_current_object(), msg)).start()
        
        return True
    except:
        return False 