# نظام إدارة الشكاوى

نظام متكامل لإدارة الشكاوى والمقترحات، مبني باستخدام Flask وBootstrap.

## المميزات

- نظام تسجيل دخول وإدارة مستخدمين متكامل
- إدارة الشكاوى والردود عليها
- نظام إشعارات متكامل
- لوحة تحكم إحصائية
- واجهة مستخدم عربية سهلة الاستخدام
- تصميم متجاوب مع جميع الأجهزة
- نظام رفع ملفات متكامل
- API للتكامل مع الأنظمة الأخرى

## المتطلبات

- Python 3.8+
- PostgreSQL أو SQLite
- وصول للإنترنت لتحميل المكتبات المطلوبة

## التثبيت

1. قم بنسخ المستودع:
```bash
git clone https://github.com/yourusername/complaints-system.git
cd complaints-system
```

2. قم بإنشاء بيئة افتراضية وتفعيلها:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. قم بتثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

4. قم بإنشاء ملف `.env` وتعبئة المتغيرات المطلوبة:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///complaints.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

5. قم بتهيئة قاعدة البيانات:
```bash
flask db upgrade
```

6. قم بتشغيل التطبيق:
```bash
python run.py
```

## الاستخدام

1. افتح المتصفح على العنوان `http://localhost:8080`
2. قم بتسجيل الدخول باستخدام:
   - البريد: admin@example.com
   - كلمة المرور: admin123

## النشر

### Heroku
```bash
heroku create your-app-name
git push heroku main
```

### VPS
1. قم بتثبيت المتطلبات:
```bash
sudo apt-get update
sudo apt-get install python3-pip python3-venv nginx
```

2. قم بإعداد Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. قم بتشغيل التطبيق باستخدام Gunicorn:
```bash
gunicorn wsgi:app --config gunicorn.conf.py
```

## المساهمة

1. قم بعمل Fork للمشروع
2. قم بإنشاء فرع جديد (`git checkout -b feature/amazing-feature`)
3. قم بعمل Commit للتغييرات (`git commit -m 'إضافة ميزة جديدة'`)
4. قم بعمل Push للفرع (`git push origin feature/amazing-feature`)
5. قم بفتح طلب Pull Request

## الترخيص

هذا المشروع مرخص تحت رخصة MIT - انظر ملف [LICENSE](LICENSE) للتفاصيل.

## الاتصال

اسمك - [@تويتر](https://twitter.com/yourusername)

رابط المشروع: [https://github.com/yourusername/complaints-system](https://github.com/yourusername/complaints-system) 