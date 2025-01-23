from app import db
from app.models import Notification

def send_notification(user, title, message, type='info', link=None):
    """
    إرسال إشعار لمستخدم
    
    :param user: كائن المستخدم
    :param title: عنوان الإشعار
    :param message: نص الإشعار
    :param type: نوع الإشعار (info, success, warning, error)
    :param link: رابط اختياري للإشعار
    :return: كائن الإشعار
    """
    notification = Notification(
        user=user,
        title=title,
        message=message,
        type=type,
        link=link
    )
    db.session.add(notification)
    db.session.commit()
    return notification 