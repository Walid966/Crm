from app import app, db
from models import User, Supervisor, Representative, Service, SubService
from werkzeug.security import generate_password_hash

def update_database():
    with app.app_context():
        # إعادة إنشاء قاعدة البيانات
        db.drop_all()
        db.create_all()
        
        print("جاري إنشاء المستخدمين...")
        
        # إنشاء مستخدم admin افتراضي
        admin = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        
        # إنشاء مستخدم support افتراضي
        support = User(
            username='support',
            email='support@example.com',
            password=generate_password_hash('support123'),
            role='support'
        )
        db.session.add(support)
        
        # إنشاء مستخدم sales افتراضي
        sales = User(
            username='sales',
            email='sales@example.com',
            password=generate_password_hash('sales123'),
            role='sales'
        )
        db.session.add(sales)
        
        print("جاري إنشاء المشرفين والمناديب...")
        
        # إنشاء مشرف
        supervisor = Supervisor(
            account_number='12345',
            name='مشرف تجريبي'
        )
        db.session.add(supervisor)
        db.session.flush()  # للحصول على الـ ID
        
        # إنشاء مندوب مرتبط بالمستخدم sales
        representative = Representative(
            account_number='67890',
            name='مندوب تجريبي',
            supervisor_id=supervisor.id,
            user_id=sales.id  # ربط المندوب بمستخدم المبيعات
        )
        db.session.add(representative)
        
        print("جاري إنشاء الخدمات...")
        
        # إنشاء خدمات تجريبية
        service1 = Service(service_type='خدمة تجريبية 1')
        service2 = Service(service_type='خدمة تجريبية 2')
        db.session.add(service1)
        db.session.add(service2)
        db.session.flush()
        
        # إنشاء خدمات فرعية
        sub_services = [
            SubService(name='خدمة فرعية 1-1', service_id=service1.id),
            SubService(name='خدمة فرعية 1-2', service_id=service1.id),
            SubService(name='خدمة فرعية 2-1', service_id=service2.id),
            SubService(name='خدمة فرعية 2-2', service_id=service2.id)
        ]
        for sub_service in sub_services:
            db.session.add(sub_service)
        
        try:
            db.session.commit()
            print("تم تحديث قاعدة البيانات بنجاح!")
            print("\nبيانات تسجيل الدخول:")
            print("المدير:")
            print("البريد: admin@example.com")
            print("كلمة المرور: admin123")
            print("\nالدعم الفني:")
            print("البريد: support@example.com")
            print("كلمة المرور: support123")
            print("\nالمبيعات:")
            print("البريد: sales@example.com")
            print("كلمة المرور: sales123")
        except Exception as e:
            print(f"حدث خطأ: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    update_database() 