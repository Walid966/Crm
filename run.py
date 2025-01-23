import os
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()

def create_folders():
    """إنشاء المجلدات المطلوبة"""
    folders = [
        os.path.join('app', 'static', 'uploads'),
        os.path.join('app', 'static', 'uploads', 'profiles'),
        os.path.join('app', 'static', 'uploads', 'complaints'),
        os.path.join('app', 'static', 'uploads', 'responses'),
        os.path.join('app', 'static', 'uploads', 'templates'),
        os.path.join('app', 'static', 'images'),
        os.path.join('app', 'static', 'sounds'),
        os.path.join('logs')
    ]
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f'تم إنشاء مجلد: {folder}')

def check_users():
    """التحقق من المستخدمين في قاعدة البيانات"""
    with app.app_context():
        users = User.query.all()
        print('\nقائمة المستخدمين في قاعدة البيانات:')
        for user in users:
            print(f'المعرف: {user.id}')
            print(f'رقم الحساب: {user.account_number}')
            print(f'اسم المستخدم: {user.username}')
            print(f'البريد الإلكتروني: {user.email}')
            print(f'الدور: {user.role}')
            print('-' * 50)

def init_db():
    """تهيئة قاعدة البيانات"""
    with app.app_context():
        print('بدء تهيئة قاعدة البيانات...')
        # إنشاء جميع الجداول
        db.create_all()
        print('تم إنشاء جميع الجداول')
        
        # إنشاء مستخدم المدير إذا لم يكن موجوداً
        admin = User.query.filter_by(email='admin@example.com').first()
        if admin:
            print('تحديث بيانات المدير...')
            admin.account_number = '5'
            try:
                db.session.commit()
                print('تم تحديث بيانات المدير بنجاح')
            except Exception as e:
                print(f'خطأ في تحديث بيانات المدير: {str(e)}')
                db.session.rollback()
        else:
            print('إنشاء حساب المدير...')
            admin = User(
                account_number='5',
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                role='admin',
                user_id=1
            )
            db.session.add(admin)
            try:
                db.session.commit()
                print('تم إنشاء حساب المدير بنجاح')
            except Exception as e:
                print(f'خطأ في إنشاء حساب المدير: {str(e)}')
                db.session.rollback()
        
        # التحقق من المستخدمين
        check_users()

if __name__ == '__main__':
    create_folders()
    init_db()
    app.run(host='0.0.0.0', port=8080, debug=True) 