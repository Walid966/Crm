from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
login.login_message_category = 'info'
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
mail = Mail()
csrf = CSRFProtect()

@login.user_loader
def load_user(id):
    from app.models import User
    return User.query.get(int(id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # تهيئة الإضافات
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60)
    mail.init_app(app)
    csrf.init_app(app)
    
    # تسجيل Blueprints
    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.routes.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    from app.routes.complaints import bp as complaints_bp
    app.register_blueprint(complaints_bp)
    
    from app.routes.users import bp as users_bp
    app.register_blueprint(users_bp)
    
    from app.routes.management import bp as management_bp
    app.register_blueprint(management_bp)
    
    from app.routes.api import bp as api_bp
    app.register_blueprint(api_bp)
    
    # إعداد التسجيل
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/compliant.log',
                                         maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('تم بدء تشغيل التطبيق')
    
    return app 