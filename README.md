# نظام إدارة الشكاوى

نظام متكامل لإدارة الشكاوى يتيح للمستخدمين تقديم ومتابعة الشكاوى بشكل فعال.

## المميزات

- تسجيل وإدارة الشكاوى
- نظام تتبع حالة الشكاوى
- إدارة المستخدمين والصلاحيات
- نظام الإشعارات
- تصدير التقارير بصيغة Excel
- واجهة مستخدم سهلة الاستخدام

## المتطلبات

- Python 3.8+
- Flask
- SQLAlchemy
- Flask-Login
- Flask-WTF
- XlsxWriter
- وغيرها (راجع ملف requirements.txt)

## التثبيت

1. قم بنسخ المستودع:
```bash
git clone https://github.com/yourusername/complaints-system.git
cd complaints-system
```

2. قم بإنشاء البيئة الافتراضية وتفعيلها:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. قم بتثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

4. قم بإنشاء ملف `.env` وتعبئة المتغيرات المطلوبة:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db
```

5. قم بتهيئة قاعدة البيانات:
```bash
flask db upgrade
```

6. قم بتشغيل التطبيق:
```bash
flask run
```

## الاستخدام

1. قم بفتح المتصفح على العنوان: `http://localhost:8080`
2. قم بتسجيل الدخول باستخدام حساب المدير الافتراضي:
   - البريد الإلكتروني: admin@example.com
   - كلمة المرور: admin123

## المساهمة

نرحب بمساهماتكم! يرجى اتباع الخطوات التالية:

1. قم بعمل Fork للمشروع
2. قم بإنشاء فرع جديد (`git checkout -b feature/amazing-feature`)
3. قم بعمل Commit للتغييرات (`git commit -m 'إضافة ميزة جديدة'`)
4. قم بعمل Push للفرع (`git push origin feature/amazing-feature`)
5. قم بفتح طلب Pull Request

## الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للمزيد من التفاصيل.

## الاتصال

اسمك - [@تويتر](https://twitter.com/yourusername)

رابط المشروع: [https://github.com/yourusername/complaints-system](https://github.com/yourusername/complaints-system) 