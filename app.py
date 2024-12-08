from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Supervisor, Representative, Service, SubService, Complaint, ComplaintResponse, Notification
from config import Config
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit, join_room
from openpyxl import Workbook
from datetime import datetime
from forms import LoginForm, RegistrationForm, ComplaintForm, SupervisorForm, RepresentativeForm, ServiceForm, SubServiceForm, ResponseForm, ProfileForm
from flask_wtf import CSRFProtect
import io

app = Flask(__name__)
app.config.from_object(Config)

# إضافة إعدادات CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5050"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

# تحديد الحد الأقصى لحجم الملف (5 ميجابايت)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# تحديد أنواع الملفات المسموح بها
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_file_size(file):
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size <= app.config['MAX_CONTENT_LENGTH']

# إضافة حماية CSRF
csrf = CSRFProtect(app)

# إعداد قاعدة البيانات
db.init_app(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# إعداد Socket.IO مع دعم CORS وتمكين WebSocket
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='gevent',
                   logger=True,
                   engineio_logger=True)

if not os.path.exists(os.path.join('static', 'uploads')):
    os.makedirs(os.path.join('static', 'uploads'))

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        print(f'المستخدم {current_user.username} اتصل بالغرفة user_{current_user.id}')

def send_notification(user_id, message):
    try:
        with app.app_context():
            # إضافة الإشعار إلى قاعدة البيانات
            notification = Notification(
                user_id=user_id,
                message=message,
                is_read=False
            )
            db.session.add(notification)
            db.session.commit()
            
            # إرسال الإشعار عبر Socket.IO
            socketio.emit('notification', {'message': message}, room=f'user_{user_id}')
            print(f'تم إرسال إشعار إلى المستخدم {user_id}: {message}')
    except Exception as e:
        print(f'خطأ في إرسال الإشعار: {str(e)}')

@socketio.on('request_notifications')
def handle_notification_request():
    if current_user.is_authenticated:
        try:
            notifications = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).all()
            for notification in notifications:
                emit('notification', {'message': notification.message})
            print(f'تم إرسال {len(notifications)} إشعارات للمستخدم {current_user.username}')
        except Exception as e:
            print(f'خطأ في إرسال الإشعارات: {str(e)}')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# إنشاء جميع الجداول في قاعدة البيانات
with app.app_context():
    db.create_all()
    # إنشاء مستخدم admin افتراضي إذا لم يكن موجوداً
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('dashboard'))
            elif user.role == 'sales':
                return redirect(url_for('complaint_form'))
            elif user.role == 'support':
                return redirect(url_for('dashboard'))
        flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # التحقق من عدم وجود البريد الإلكتروني مسبقاً
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('البريد الإلكتروني مستخدم بالفعل', 'error')
            return render_template('register.html', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            role='sales'
        )
        db.session.add(user)
        db.session.commit()
        flash('تم إنشاء الحساب بنجاح', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('complaint_form'))
    
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template('dashboard.html', complaints=complaints)

@app.route('/manage_data')
@login_required
def manage_data():
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    supervisor_form = SupervisorForm()
    representative_form = RepresentativeForm()
    service_form = ServiceForm()
    sub_service_form = SubServiceForm()
    
    supervisors = Supervisor.query.all()
    services = Service.query.all()
    
    return render_template('manage_data.html',
                         supervisors=supervisors,
                         services=services,
                         supervisor_form=supervisor_form,
                         representative_form=representative_form,
                         service_form=service_form,
                         sub_service_form=sub_service_form)

@app.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/complaint_form', methods=['GET', 'POST'])
@login_required
def complaint_form():
    if current_user.role != 'sales':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('index'))
    
    form = ComplaintForm()
    
    # تحميل المشرفين
    supervisors = Supervisor.query.all()
    form.supervisor_account.choices = [(0, 'اختر المشرف')] + [(s.id, f"{s.name} ({s.account_number})") for s in supervisors]
    
    # تحميل الخدمات
    services = Service.query.all()
    form.service_type.choices = [(0, 'اختر الخدمة')] + [(s.id, s.service_type) for s in services]
    
    # تحميل المناديب والخدمات الفرعية عند اختيار المشرف والخدمة
    if form.supervisor_account.data and form.supervisor_account.data != '0':
        supervisor = Supervisor.query.get(form.supervisor_account.data)
        if supervisor:
            form.representative_account.choices = [(0, 'اختر المندوب')] + [
                (r.id, f"{r.name} ({r.account_number})") 
                for r in supervisor.representatives
            ]
    else:
        form.representative_account.choices = [(0, 'اختر المندوب')]
    
    if form.service_type.data and form.service_type.data != '0':
        service = Service.query.get(form.service_type.data)
        if service:
            form.sub_service.choices = [(0, 'اختر الخدمة الفرعية')] + [(s.id, s.name) for s in service.sub_services]
    else:
        form.sub_service.choices = [(0, 'اختر الخدمة الفرعية')]
    
    if form.validate_on_submit():
        try:
            # التحقق من أ القيم المختارة ليست صفر
            if int(form.supervisor_account.data) == 0:
                flash('يجب اختيار المشرف', 'error')
                return render_template('complaint_form.html', form=form)
            if int(form.representative_account.data) == 0:
                flash('يجب اختيار المندوب', 'error')
                return render_template('complaint_form.html', form=form)
            if int(form.service_type.data) == 0:
                flash('يجب اختيار نوع الخدمة', 'error')
                return render_template('complaint_form.html', form=form)
            if int(form.sub_service.data) == 0:
                flash('يجب اختيار الخدمة الفرعية', 'error')
                return render_template('complaint_form.html', form=form)

            image_path = None
            if form.image.data:
                image_path = save_uploaded_file(form.image.data)
                if not image_path:
                    flash('حدث خطأ أثناء رفع الملف', 'error')
                    return render_template('complaint_form.html', form=form)
            
            complaint = Complaint(
                representative_id=form.representative_account.data,
                merchant_account=form.merchant_account.data,
                service_id=form.service_type.data,
                sub_service_id=form.sub_service.data,
                transaction_number=form.transaction_number.data,
                notes=form.notes.data,
                image_path=image_path,
                status='pending'
            )
            db.session.add(complaint)
            db.session.commit()
            
            # إضافة إشعار للمشرفين والدعم الفني
            representative = Representative.query.get(form.representative_account.data)
            supervisor = representative.supervisor
            notification_message = f'تم إضافة شكوى جديدة من المندوب {representative.name}'
            
            if supervisor and supervisor.user_id:
                notification = Notification(
                    user_id=supervisor.user_id,
                    complaint_id=complaint.id,
                    message=notification_message
                )
                db.session.add(notification)
                send_notification(supervisor.user_id, notification_message)
            
            support_users = User.query.filter_by(role='support').all()
            for user in support_users:
                notification = Notification(
                    user_id=user.id,
                    complaint_id=complaint.id,
                    message=notification_message
                )
                db.session.add(notification)
                send_notification(user.id, notification_message)
            
            db.session.commit()
            socketio.emit('new_complaint', {'id': complaint.id})
            flash('تم إرسال الشكوى بنجاح', 'success')
            return redirect(url_for('complaint_responses'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إرسال الشكوى: {str(e)}', 'error')
            return render_template('complaint_form.html', form=form)
    
    return render_template('complaint_form.html', form=form)

@app.route('/complaint_responses')
@login_required
def complaint_responses():
    try:
        if current_user.role == 'sales':
            # البحث عن المندوب المرتبط بالمستخدم الحالي
            representative = Representative.query.filter_by(user_id=current_user.id).first()
            if representative:
                print(f"تم العثور على المندوب: {representative.name}")
                complaints = Complaint.query.filter_by(representative_id=representative.id)\
                    .order_by(Complaint.created_at.desc()).all()
                print(f"عدد الشكاوى: {len(complaints)}")
            else:
                print("لم يتم العثور على مندوب مرتبط بالمستخدم")
                complaints = []
        else:
            # المدير والدعم الفني يرون جميع الشكاوى
            complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
            print(f"عدد الشكاوى للمدير/الدعم: {len(complaints)}")
        
        return render_template('complaint_responses.html', complaints=complaints)
    except Exception as e:
        print(f"حدث خطأ: {str(e)}")
        flash('حدث خطأ أثناء تح��يل الشكاوى', 'error')
        return render_template('complaint_responses.html', complaints=[])

@app.route('/add_response/<int:complaint_id>', methods=['POST'])
@login_required
def add_response(complaint_id):
    if current_user.role not in ['admin', 'support']:
        flash('غير مصرح لك بإضافة رد', 'error')
        return redirect(url_for('complaint_responses'))
    
    complaint = Complaint.query.get_or_404(complaint_id)
    response_text = request.form.get('response_text')
    new_status = request.form.get('status')
    
    if not response_text:
        flash('الرجاء إدخال نص الرد', 'error')
        return redirect(url_for('complaint_responses'))
    
    try:
        # إضافة الرد
        response = ComplaintResponse(
            complaint_id=complaint_id,
            user_id=current_user.id,
            response_text=response_text
        )
        db.session.add(response)
        
        # تحديث حالة الشكوى
        if new_status:
            complaint.status = new_status
        
        # إضافة إشعار للمندوب
        if complaint.representative and complaint.representative.user_id:
            notification = Notification(
                user_id=complaint.representative.user_id,
                complaint_id=complaint_id,
                message=f'تم إضافة رد جديد على شكواك من قبل {current_user.username}'
            )
            db.session.add(notification)
            send_notification(complaint.representative.user_id, notification.message)
        
        db.session.commit()

        # إرسال حدث تحديث الشكاوى
        socketio.emit('new_complaint', {'id': complaint_id})
        
        flash('تم إضافة الرد بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إضافة الرد: {str(e)}', 'error')
    
    return redirect(url_for('complaint_responses'))

@app.route('/get_representatives/<int:supervisor_id>')
def get_representatives(supervisor_id):
    supervisor = Supervisor.query.get_or_404(supervisor_id)
    representatives = [
        {'id': r.id, 'name': f"{r.name} ({r.account_number})"} 
        for r in supervisor.representatives
    ]
    return jsonify(representatives)

@app.route('/get_sub_services/<int:service_id>')
def get_sub_services(service_id):
    service = Service.query.get_or_404(service_id)
    sub_services = [
        {'id': s.id, 'name': s.name} 
        for s in service.sub_services
    ]
    return jsonify(sub_services)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_supervisor', methods=['POST'])
@login_required
def add_supervisor():
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    form = SupervisorForm()
    if form.validate_on_submit():
        supervisor = Supervisor(
            account_number=form.account_number.data,
            name=form.name.data
        )
        db.session.add(supervisor)
        db.session.commit()

        # إضافة المناديب
        rep_account_numbers = request.form.getlist('rep_account_numbers[]')
        rep_names = request.form.getlist('rep_names[]')
        
        for acc, name in zip(rep_account_numbers, rep_names):
            if acc and name:  # التأكد من أن الحقول ليست فارغة
                representative = Representative(
                    account_number=acc,
                    name=name,
                    supervisor_id=supervisor.id
                )
                db.session.add(representative)
        
        db.session.commit()
        flash('تم إضافة المشرف والمناديب بنجاح', 'success')
    return redirect(url_for('manage_data'))

@app.route('/add_representative/<int:supervisor_id>', methods=['GET', 'POST'])
@login_required
def add_representative(supervisor_id):
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    form = RepresentativeForm()
    supervisor = Supervisor.query.get_or_404(supervisor_id)
    
    if form.validate_on_submit():
        # التحقق من عدم وجود رقم حساب مكرر
        existing_representative = Representative.query.filter_by(
            account_number=form.account_number.data
        ).first()
        
        if existing_representative:
            flash('رقم الحساب مستخدم بالفعل', 'error')
            return render_template('add_representative.html', form=form, supervisor=supervisor)
        
        try:
            representative = Representative(
                account_number=form.account_number.data,
                name=form.name.data,
                supervisor_id=supervisor_id
            )
            db.session.add(representative)
            db.session.commit()
            flash('تم إضافة المندوب بنجاح', 'success')
            return redirect(url_for('manage_data'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إضافة المندوب', 'error')
            return render_template('add_representative.html', form=form, supervisor=supervisor)
    
    return render_template('add_representative.html', form=form, supervisor=supervisor)

@app.route('/add_service', methods=['POST'])
@login_required
def add_service():
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    form = ServiceForm()
    if form.validate_on_submit():
        service = Service(service_type=form.service_type.data)
        db.session.add(service)
        db.session.commit()

        # إضافة الخدمات الفرعية
        sub_service_names = request.form.getlist('sub_service_names[]')
        
        for name in sub_service_names:
            if name:  # التأكد من أن الحقل ليس فارغاً
                sub_service = SubService(
                    name=name,
                    service_id=service.id
                )
                db.session.add(sub_service)
        
        db.session.commit()
        flash('تم إضافة الخدمة والخدمات الفرعية بنجاح', 'success')
    return redirect(url_for('manage_data'))

@app.route('/add_sub_service/<int:service_id>', methods=['POST'])
@login_required
def add_sub_service(service_id):
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    form = SubServiceForm()
    if form.validate_on_submit():
        sub_service = SubService(
            name=form.name.data,
            service_id=service_id
        )
        db.session.add(sub_service)
        db.session.commit()
        flash('تم إضافة الخدمة الفرعية بنجاح', 'success')
    return redirect(url_for('manage_data'))

@app.route('/edit_user/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    role = request.form.get('role')
    if role in ['admin', 'support', 'sales']:
        user.role = role
        db.session.commit()
        flash('تم تحديث بيانات المستخدم بنجاح', 'success')
    return redirect(url_for('manage_users'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:  # لا يمكن للمستخدم حذف نفسه
        db.session.delete(user)
        db.session.commit()
        flash('تم حذف المستخدم بنجاح', 'success')
    return redirect(url_for('manage_users'))

@app.route('/edit_supervisor/<int:supervisor_id>', methods=['POST'])
@login_required
def edit_supervisor(supervisor_id):
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    supervisor = Supervisor.query.get_or_404(supervisor_id)
    
    # تحديث بيانات المشرف
    supervisor.account_number = request.form.get('account_number')
    supervisor.name = request.form.get('name')
    
    # إضافة مناديب جدد
    new_rep_account_numbers = request.form.getlist('new_rep_account_numbers[]')
    new_rep_names = request.form.getlist('new_rep_names[]')
    
    for acc, name in zip(new_rep_account_numbers, new_rep_names):
        if acc and name:  # التأكد من أن الحقول ليست فارغة
            representative = Representative(
                account_number=acc,
                name=name,
                supervisor_id=supervisor.id
            )
            db.session.add(representative)
    
    try:
        db.session.commit()
        flash('تم تحديث بيانات المشرف والمناديب بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء تحديث البيانات', 'error')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('manage_data'))

@app.route('/delete_supervisor/<int:supervisor_id>', methods=['POST'])
@login_required
def delete_supervisor(supervisor_id):
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    supervisor = Supervisor.query.get_or_404(supervisor_id)
    db.session.delete(supervisor)
    db.session.commit()
    flash('تم حذف المشرف بنجاح', 'success')
    return redirect(url_for('manage_data'))

@app.route('/edit_representative/<int:representative_id>', methods=['POST'])
@login_required
def edit_representative(representative_id):
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    representative = Representative.query.get_or_404(representative_id)
    form = RepresentativeForm()
    if form.validate_on_submit():
        representative.account_number = form.account_number.data
        representative.name = form.name.data
        db.session.commit()
        flash('تم تحديث بيانات المندوب بنجاح', 'success')
    return redirect(url_for('manage_data'))

@app.route('/delete_representative/<int:representative_id>', methods=['POST'])
@login_required
def delete_representative(representative_id):
    if current_user.role not in ['admin', 'support']:
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'}), 403
    
    try:
        representative = Representative.query.get_or_404(representative_id)
        db.session.delete(representative)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'تم حذف المندوب بنجاح'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف المندوب'
        }), 500

@app.route('/edit_service/<int:service_id>', methods=['POST'])
@login_required
def edit_service(service_id):
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    service = Service.query.get_or_404(service_id)
    form = ServiceForm()
    
    if form.validate_on_submit():
        service.service_type = form.service_type.data
        
        # إضافة خدمات فرعية جديدة
        new_sub_service_names = request.form.getlist('new_sub_service_names[]')
        
        for name in new_sub_service_names:
            if name:  # التأكد من أن الحقل ليس فارغاً
                sub_service = SubService(
                    name=name,
                    service_id=service.id
                )
                db.session.add(sub_service)
        
        db.session.commit()
        flash('تم تحديث الخدمة والخدمات الفرعية بنجاح', 'success')
    return redirect(url_for('manage_data'))

@app.route('/delete_service/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('تم حذف الخدمة بنجاح', 'success')
    return redirect(url_for('manage_data'))

@app.route('/update_complaint_status/<int:complaint_id>', methods=['POST'])
@login_required
def update_complaint_status(complaint_id):
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    complaint = Complaint.query.get_or_404(complaint_id)
    status = request.form.get('status')
    if status in ['pending', 'in_progress', 'completed']:
        old_status = complaint.status
        complaint.status = status
        db.session.commit()
        
        # إضافة إشعار للمستخدم صاحب الشكوى
        notification = Notification(
            user_id=complaint.representative.user_id,
            complaint_id=complaint_id,
            message=f'تم تغيير حالة الشكوى رقم {complaint_id} من {old_status} إلى {status}'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('تم تحديث حالة الشكوى بنجاح', 'success')
    return redirect(url_for('dashboard'))

@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    return render_template('notifications.html', notifications=notifications)

@app.route('/mark_notification_read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        flash('غير مصرح لك بهذه العملية', 'error')
        return redirect(url_for('notifications'))
    
    notification.is_read = True
    db.session.commit()
    return redirect(url_for('notifications'))

@app.route('/statistics')
@login_required
def statistics():
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    total_complaints = Complaint.query.count()
    completed_complaints = Complaint.query.filter_by(status='completed').count()
    in_progress_complaints = Complaint.query.filter_by(status='in_progress').count()
    
    return render_template('statistics.html',
                         total_complaints=total_complaints,
                         completed_complaints=completed_complaints,
                         in_progress_complaints=in_progress_complaints)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.current_password.data):
            current_user.username = form.username.data
            current_user.email = form.email.data
            if form.new_password.data:
                current_user.password = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('تم تحديث الملف الشخصي بنجاح', 'success')
            return redirect(url_for('profile'))
        else:
            flash('كلمة المرور الحالية غير صحيحة', 'error')
    return render_template('profile.html', form=form)

@app.route('/export_complaints')
@login_required
def export_complaints():
    if current_user.role not in ['admin', 'support', 'sales']:
        flash('غير مصرح لك بتصدير الشكاوى', 'error')
        return redirect(url_for('index'))
        
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "الشكاوى"
        
        headers = [
            'رقم الشكوى',
            'رقم حساب الاجر',
            'المندوب',
            'المشرف',
            'نوع الخدمة',
            'الخدمة الفرعية',
            'رقم العملية',
            'الملاحظات',
            'الحالة',
            'تاريخ الإنشاء',
            'آخر رد',
            'حالة الرد'
        ]
        ws.append(headers)
        
        if current_user.role == 'sales':
            representative = Representative.query.filter_by(user_id=current_user.id).first()
            if representative:
                complaints = Complaint.query.filter_by(representative_id=representative.id)\
                    .order_by(Complaint.created_at.desc()).all()
            else:
                complaints = []
        else:
            complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
        
        for complaint in complaints:
            try:
                last_response = ComplaintResponse.query.filter_by(complaint_id=complaint.id)\
                    .order_by(ComplaintResponse.created_at.desc()).first()
                
                row = [
                    complaint.id,
                    complaint.merchant_account,
                    complaint.representative.name if complaint.representative else 'غير محدد',
                    complaint.representative.supervisor.name if complaint.representative and complaint.representative.supervisor else 'غير محدد',
                    complaint.service.service_type if complaint.service else 'غير محدد',
                    complaint.sub_service.name if complaint.sub_service else 'غير محدد',
                    complaint.transaction_number,
                    complaint.notes,
                    complaint.status,
                    complaint.created_at.strftime('%Y-%m-%d %H:%M'),
                    last_response.response_text if last_response else 'لا يوجد رد',
                    last_response.created_at.strftime('%Y-%m-%d %H:%M') if last_response else '-'
                ]
                ws.append(row)
            except Exception as e:
                print(f"خطأ في معالجة الشكوى {complaint.id}: {str(e)}")
                continue
        
        # تنسيق العرض
        for column in ws.columns:
            max_length = 0
            column = list(column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column[0].column_letter].width = adjusted_width
        
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        filename = f"complaints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"خطأ في تصدير الشكاوى: {str(e)}")
        flash('حدث خطأ أثناء تصدير الشكاوى', 'error')
        return redirect(url_for('complaint_responses'))

def delete_file(filename):
    if filename:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/delete_complaint/<int:complaint_id>', methods=['POST'])
@login_required
def delete_complaint(complaint_id):
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    complaint = Complaint.query.get_or_404(complaint_id)
    # حذف الملف المرفق إذا وجد
    delete_file(complaint.image_path)
    db.session.delete(complaint)
    db.session.commit()
    flash('تم حذف الشكوى بنجاح', 'success')
    return redirect(url_for('dashboard'))

@app.route('/advanced_statistics')
@login_required
def advanced_statistics():
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    # إحصائيات عامة
    supervisors_count = Supervisor.query.count()
    representatives_count = Representative.query.count()
    services_count = Service.query.count()
    users_count = User.query.count()
    
    # إحصائيات الحالات
    status_stats = {
        'pending': Complaint.query.filter_by(status='pending').count(),
        'in_progress': Complaint.query.filter_by(status='in_progress').count(),
        'completed': Complaint.query.filter_by(status='completed').count()
    }
    
    # إحصائيات الخدمات
    services = Service.query.all()
    service_labels = [service.service_type for service in services]
    service_data = [Complaint.query.filter_by(service_id=service.id).count() 
                   for service in services]
    
    # إح��ائيات المشرفين
    supervisor_stats = []
    for supervisor in Supervisor.query.all():
        complaints = Complaint.query.join(Representative)\
            .filter(Representative.supervisor_id == supervisor.id).all()
        total = len(complaints)
        if total > 0:
            completed = len([c for c in complaints if c.status == 'completed'])
            pending = len([c for c in complaints if c.status == 'pending'])
            in_progress = len([c for c in complaints if c.status == 'in_progress'])
            completion_rate = (completed / total) * 100
        else:
            completed = pending = in_progress = 0
            completion_rate = 0
            
        supervisor_stats.append({
            'supervisor_name': supervisor.name,
            'total_complaints': total,
            'completed_complaints': completed,
            'pending_complaints': pending,
            'in_progress_complaints': in_progress,
            'completion_rate': completion_rate
        })
    
    return render_template('advanced_statistics.html',
                         supervisors_count=supervisors_count,
                         representatives_count=representatives_count,
                         services_count=services_count,
                         users_count=users_count,
                         status_stats=status_stats,
                         service_labels=service_labels,
                         service_data=service_data,
                         supervisor_stats=supervisor_stats)

@app.route('/export_advanced_report')
@login_required
def export_advanced_report():
    if current_user.role not in ['admin', 'support']:
        return redirect(url_for('index'))
    
    wb = Workbook()
    ws = wb.active
    ws.title = "تقرير تفصيلي"
    
    # إضافة العناوين
    headers = ['المشرف', 'عدد الشكاوى', 'قيد الانتظار', 'يد المعلجة', 
              'مكتملة', 'نسبة الإنجاز']
    ws.append(headers)
    
    # إضافة البيانات
    for supervisor in Supervisor.query.all():
        complaints = Complaint.query.join(Representative)\
            .filter(Representative.supervisor_id == supervisor.id).all()
        total = len(complaints)
        if total > 0:
            completed = len([c for c in complaints if c.status == 'completed'])
            pending = len([c for c in complaints if c.status == 'pending'])
            in_progress = len([c for c in complaints if c.status == 'in_progress'])
            completion_rate = (completed / total) * 100
        else:
            completed = pending = in_progress = 0
            completion_rate = 0
            
        ws.append([
            supervisor.name,
            total,
            pending,
            in_progress,
            completed,
            f"{completion_rate:.2f}%"
        ])
    
    # حفظ الملف
    filename = f'advanced_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    wb.save(filepath)
    
    return send_file(filepath, as_attachment=True)

@app.route('/unread_notifications_count')
@login_required
def unread_notifications_count():
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    return jsonify({'count': count})

@app.route('/get_notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .order_by(Notification.created_at.desc()).limit(5).all()
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')
    } for n in notifications])

@app.route('/mark_all_notifications_read')
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({Notification.is_read: True})
    db.session.commit()
    return redirect(url_for('notifications'))

@app.route('/delete_sub_service/<int:sub_service_id>', methods=['POST'])
@login_required
def delete_sub_service(sub_service_id):
    if current_user.role not in ['admin', 'support']:
        return jsonify({'success': False, 'message': 'غير مصرح لك بهذه العملية'}), 403
    
    try:
        sub_service = SubService.query.get_or_404(sub_service_id)
        db.session.delete(sub_service)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم حذف الخدمة الفرعية بنجاح'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف الخدمة الفرعية'
        }), 500

@app.route('/change_user_password/<int:user_id>', methods=['POST'])
@login_required
def change_user_password(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('كلمات المرور غير متطابقة', 'error')
        return redirect(url_for('manage_users'))
    
    if len(new_password) < 6:
        flash('يجب أن تكون كلمة المرور 6 أحرف على الأقل', 'error')
        return redirect(url_for('manage_users'))
    
    try:
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('تم تغيير كلمة المرور بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء تغيير كلمة المرور', 'error')
    
    return redirect(url_for('manage_users'))

# إضافة معالجة الخطأ في حالة فشل تحمي�� الملف
def save_uploaded_file(file):
    try:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = os.path.join('static', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            return filename
        return None
    except Exception as e:
        print(f"خطأ في حفظ الملف: {str(e)}")
        return None

if __name__ == '__main__':
    # التأكد من وجود مجلد الملفات المرفقة
    upload_dir = os.path.join('static', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # تحديد المنفذ من متغيرات البيئة أو استخدام 5050 كقيمة افتراضية
    port = int(os.environ.get('PORT', 5050))
    if os.environ.get('VERCEL_ENV') == 'production':
        app.run()
    else:
        socketio.run(app, 
                    host='0.0.0.0',
                    port=port,
                    debug=False) 