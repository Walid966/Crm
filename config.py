import os
from dotenv import load_dotenv
from datetime import timedelta

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

class Config:
    # إعدادات عامة
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 ميجابايت
    
    # تعيين مجلد التحميل كمسار مطلق
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'complaints.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات البريد الإلكتروني
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # إعدادات المدير
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
    
    # إعدادات الأمان
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600  # ساعة واحدة
    REMEMBER_COOKIE_DURATION = 2592000  # 30 يوم
    
    # إعدادات التخزين المؤقت
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # سنة واحدة
    TEMPLATES_AUTO_RELOAD = True
    
    # إعدادات الشركة
    COMPANY_NAME = os.environ.get('COMPANY_NAME', 'نظام إدارة الشكاوى')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@example.com')
    
    # إعدادات الإشعارات
    NOTIFICATIONS_PER_PAGE = 10
    NOTIFICATIONS_CHECK_INTERVAL = 60  # ثانية
    
    # إعدادات الشكاوى
    COMPLAINTS_PER_PAGE = 10
    COMPLAINT_RESPONSE_TIMEOUT = 24  # ساعة
    AUTO_CLOSE_COMPLAINTS = True
    AUTO_CLOSE_AFTER = 72  # ساعة
    
    # إعدادات التصدير
    EXCEL_MIMETYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    PDF_MIMETYPE = 'application/pdf'
    
    # إعدادات التسجيل
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 ميجابايت
    LOG_BACKUP_COUNT = 5
    
    @staticmethod
    def init_app(app):
        """تهيئة التطبيق"""
        # إنشاء مجلد التحميل إذا لم يكن موجوداً
        uploads_dir = os.path.join(app.static_folder, 'uploads')
        profiles_dir = os.path.join(uploads_dir, 'profiles')
        
        # إنشاء المجلدات إذا لم تكن موجودة
        os.makedirs(uploads_dir, exist_ok=True)
        os.makedirs(profiles_dir, exist_ok=True) 