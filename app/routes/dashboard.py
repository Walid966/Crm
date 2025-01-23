from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Complaint, Service, Supervisor, Representative, Notification, User
from app import db
from sqlalchemy import func, case, extract, text
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils import save_file, delete_file
from app.forms.profile import ProfileForm
from app.utils.decorators import admin_required

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    """الصفحة الرئيسية للوحة التحكم"""
    
    # إحصائيات الشكاوى
    complaints_query = Complaint.query
    
    # تقييد الشكاوى لمستخدمي المبيعات
    if current_user.role == 'sales':
        complaints_query = complaints_query.filter_by(user_id=current_user.id)
    
    # إحصائيات حسب الحالة
    total_complaints = complaints_query.count()
    pending_complaints = complaints_query.filter_by(status='pending').count()
    in_progress_complaints = complaints_query.filter_by(status='in_progress').count()
    resolved_complaints = complaints_query.filter_by(status='resolved').count()
    rejected_complaints = complaints_query.filter_by(status='rejected').count()
    
    # آخر الشكاوى
    recent_complaints = complaints_query.order_by(Complaint.created_at.desc()).limit(10).all()
    
    # قاموس تسميات الحالات
    status_labels = {
        'pending': 'قيد الانتظار',
        'in_progress': 'قيد المعالجة',
        'resolved': 'تم الحل',
        'rejected': 'مرفوضة'
    }
    
    # قاموس ألوان الحالات
    status_colors = {
        'pending': 'warning',
        'in_progress': 'info',
        'resolved': 'success',
        'rejected': 'danger'
    }
    
    return render_template('dashboard/index.html',
                         total_complaints=total_complaints,
                         pending_complaints=pending_complaints,
                         in_progress_complaints=in_progress_complaints,
                         resolved_complaints=resolved_complaints,
                         rejected_complaints=rejected_complaints,
                         recent_complaints=recent_complaints,
                         status_labels=status_labels,
                         status_colors=status_colors)

@bp.route('/statistics')
@login_required
def statistics():
    try:
        # بناء الاستعلام الأساسي
        complaints_query = Complaint.query
        
        # تقييد الشكاوى لمستخدمي المبيعات
        if current_user.role == 'sales':
            complaints_query = complaints_query.filter_by(user_id=current_user.id)
        
        # إحصائيات عامة
        stats = {
            'total_complaints': complaints_query.count(),
            'resolved_complaints': complaints_query.filter_by(status='resolved').count(),
            'pending_complaints': complaints_query.filter_by(status='pending').count(),
            'in_progress_complaints': complaints_query.filter_by(status='in_progress').count()
        }
        
        # إحصائيات المشرفين
        supervisors_query = db.session.query(
            Supervisor.name,
            func.count(Complaint.id).label('complaints_count')
        ).join(Complaint)
        
        if current_user.role == 'sales':
            supervisors_query = supervisors_query.filter(Complaint.user_id == current_user.id)
            
        supervisors_data = supervisors_query.group_by(Supervisor.id).all()
        
        stats['supervisors_data'] = {
            'labels': [s[0] for s in supervisors_data],
            'values': [s[1] for s in supervisors_data]
        }
        
        # إحصائيات الخدمات
        services_query = db.session.query(
            Service.name,
            func.count(Complaint.id).label('complaints_count')
        ).join(Complaint)
        
        if current_user.role == 'sales':
            services_query = services_query.filter(Complaint.user_id == current_user.id)
            
        services_data = services_query.group_by(Service.id).all()
        
        stats['services_data'] = {
            'labels': [s[0] for s in services_data],
            'values': [s[1] for s in services_data]
        }
        
        # إحصائيات المناديب
        representatives_query = db.session.query(
            Representative.name,
            func.count(Complaint.id).label('complaints_count')
        ).join(Complaint)
        
        if current_user.role == 'sales':
            representatives_query = representatives_query.filter(Complaint.user_id == current_user.id)
            
        representatives_data = representatives_query.group_by(Representative.id).all()
        
        stats['representatives_data'] = {
            'labels': [r[0] for r in representatives_data],
            'values': [r[1] for r in representatives_data]
        }
        
        # إحصائيات الحالة
        status_query = db.session.query(
            Complaint.status,
            func.count(Complaint.id).label('count')
        )
        
        if current_user.role == 'sales':
            status_query = status_query.filter(Complaint.user_id == current_user.id)
            
        status_data = status_query.group_by(Complaint.status).all()
        
        stats['status_data'] = {
            'labels': ['قيد الانتظار', 'قيد المعالجة', 'تم الحل', 'مرفوضة'],
            'values': [
                next((s[1] for s in status_data if s[0] == 'pending'), 0),
                next((s[1] for s in status_data if s[0] == 'in_progress'), 0),
                next((s[1] for s in status_data if s[0] == 'resolved'), 0),
                next((s[1] for s in status_data if s[0] == 'rejected'), 0)
            ]
        }
        
        # أفضل المشرفين
        top_supervisors_query = db.session.query(
            Supervisor.name,
            func.count(Complaint.id).label('total_complaints'),
            (func.sum(case([(Complaint.status == 'resolved', 1)], else_=0)) * 100.0 / 
             func.count(Complaint.id)).label('resolution_rate'),
            func.avg(
                case([(Complaint.status == 'resolved',
                      extract('epoch', Complaint.updated_at - Complaint.created_at) / 3600)],
                     else_=None)
            ).label('avg_resolution_time')
        ).join(Complaint)
        
        if current_user.role == 'sales':
            top_supervisors_query = top_supervisors_query.filter(Complaint.user_id == current_user.id)
            
        top_supervisors = top_supervisors_query.group_by(Supervisor.id).order_by(text('resolution_rate DESC')).limit(5).all()
        
        stats['top_supervisors'] = [{
            'name': s[0],
            'total_complaints': s[1],
            'resolution_rate': float(s[2] or 0),
            'avg_resolution_time': f"{float(s[3] or 0):.1f} ساعة" if s[3] else 'غير متوفر'
        } for s in top_supervisors]
        
        # أفضل المناديب
        top_representatives_query = db.session.query(
            Representative.name,
            func.count(Complaint.id).label('total_complaints'),
            (func.sum(case([(Complaint.status == 'resolved', 1)], else_=0)) * 100.0 / 
             func.count(Complaint.id)).label('resolution_rate'),
            func.avg(
                case([(Complaint.status == 'resolved',
                      extract('epoch', Complaint.updated_at - Complaint.created_at) / 3600)],
                     else_=None)
            ).label('avg_resolution_time')
        ).join(Complaint)
        
        if current_user.role == 'sales':
            top_representatives_query = top_representatives_query.filter(Complaint.user_id == current_user.id)
            
        top_representatives = top_representatives_query.group_by(Representative.id).order_by(text('resolution_rate DESC')).limit(5).all()
        
        stats['top_representatives'] = [{
            'name': r[0],
            'total_complaints': r[1],
            'resolution_rate': float(r[2] or 0),
            'avg_resolution_time': f"{float(r[3] or 0):.1f} ساعة" if r[3] else 'غير متوفر'
        } for r in top_representatives]
        
        return render_template('dashboard/statistics.html', stats=stats)
        
    except Exception as e:
        current_app.logger.error(f'خطأ في صفحة الإحصائيات: {str(e)}')
        flash('حدث خطأ أثناء تحميل الإحصائيات', 'error')
        return redirect(url_for('dashboard.index'))

@bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=10)
    
    # تحديث حالة الإشعارات إلى مقروءة
    for notification in notifications.items:
        if not notification.read:
            notification.read = True
    db.session.commit()
    
    return render_template('dashboard/notifications.html', notifications=notifications)

@bp.route('/notification/<int:id>')
@login_required
def notification(id):
    """معالجة النقر على الإشعار"""
    notification = Notification.query.get_or_404(id)
    
    # التحقق من ملكية الإشعار
    if notification.user_id != current_user.id:
        flash('غير مصرح لك بالوصول إلى هذا الإشعار', 'error')
        return redirect(url_for('dashboard.index'))
    
    # حفظ الرابط
    redirect_url = notification.link
    
    # التحقق من وجود رابط صالح
    if not redirect_url:
        flash('الرابط غير متوفر', 'error')
        return redirect(url_for('dashboard.notifications'))
    
    # حذف الإشعار
    try:
        db.session.delete(notification)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f'خطأ في حذف الإشعار: {str(e)}')
        db.session.rollback()
    
    # إعادة التوجيه إلى الرابط
    return redirect(redirect_url)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """صفحة الملف الشخصي"""
    form = ProfileForm(
        original_username=current_user.username,
        original_email=current_user.email,
        original_account_number=current_user.account_number
    )
    
    if form.validate_on_submit():
        current_user.account_number = form.account_number.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        if form.current_password.data and form.new_password.data:
            if current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
            else:
                flash('كلمة المرور الحالية غير صحيحة', 'danger')
                return redirect(url_for('dashboard.profile'))
        
        if form.profile_image.data:
            file = save_file(form.profile_image.data)
            if current_user.profile_image and current_user.profile_image != 'default-avatar.png':
                delete_file(current_user.profile_image)
            current_user.profile_image = file
        
        db.session.commit()
        flash('تم تحديث الملف الشخصي بنجاح', 'success')
        return redirect(url_for('dashboard.profile'))
    
    elif request.method == 'GET':
        form.account_number.data = current_user.account_number
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('dashboard/profile.html', form=form)

@bp.route('/info')
@login_required
def info():
    """صفحة معلومات النظام"""
    # معلومات عامة
    system_info = {
        'total_complaints': Complaint.query.count(),
        'total_supervisors': Supervisor.query.count(),
        'total_representatives': Representative.query.count(),
        'total_services': Service.query.count()
    }
    
    # إحصائيات الشكاوى
    complaints_stats = {
        'pending': Complaint.query.filter_by(status='pending').count(),
        'in_progress': Complaint.query.filter_by(status='in_progress').count(),
        'resolved': Complaint.query.filter_by(status='resolved').count(),
        'rejected': Complaint.query.filter_by(status='rejected').count()
    }
    
    # أحدث الشكاوى
    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()
    
    # أكثر المشرفين نشاطاً
    active_supervisors = db.session.query(
        Supervisor.name,
        func.count(Complaint.id).label('complaints_count')
    ).join(Complaint).group_by(Supervisor.id).order_by(text('complaints_count DESC')).limit(5).all()
    
    # أكثر المناديب نشاطاً
    active_representatives = db.session.query(
        Representative.name,
        func.count(Complaint.id).label('complaints_count')
    ).join(Complaint).group_by(Representative.id).order_by(text('complaints_count DESC')).limit(5).all()
    
    return render_template('dashboard/info.html',
                         system_info=system_info,
                         complaints_stats=complaints_stats,
                         recent_complaints=recent_complaints,
                         active_supervisors=active_supervisors,
                         active_representatives=active_representatives)

@bp.route('/notifications/delete-all', methods=['POST'])
@login_required
def delete_all_notifications():
    """حذف جميع الإشعارات للمستخدم الحالي"""
    try:
        Notification.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف جميع الإشعارات بنجاح'})
    except Exception as e:
        current_app.logger.error(f'خطأ في حذف الإشعارات: {str(e)}')
        db.session.rollback()
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء حذف الإشعارات'})

@bp.route('/users')
@login_required
def users():
    """صفحة إدارة المستخدمين"""
    if current_user.role not in ['admin', 'support']:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard.index'))
        
    users = User.query.all()
    return render_template('dashboard/users.html', users=users)

@bp.route('/user/add', methods=['POST'])
@login_required
def add_user():
    """إضافة مستخدم جديد"""
    if current_user.role not in ['admin', 'support']:
        return jsonify({'success': False, 'message': 'غير مصرح لك بإضافة مستخدمين'})
        
    data = request.get_json()
    
    try:
        # التحقق من عدم وجود مستخدم بنفس اسم المستخدم أو البريد الإلكتروني أو رقم الحساب
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'اسم المستخدم موجود بالفعل'})
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'البريد الإلكتروني موجود بالفعل'})
        
        if User.query.filter_by(account_number=data['account_number']).first():
            return jsonify({'success': False, 'message': 'رقم الحساب موجود بالفعل'})
        
        # إنشاء مستخدم جديد
        user = User(
            account_number=data['account_number'],
            username=data['username'],
            email=data['email'],
            role=data['role'],
            supervisor_account=data.get('supervisor_account'),
            supervisor_name=data.get('supervisor_name')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'تم إضافة المستخدم بنجاح',
            'user': {
                'id': user.id
            }
        })
    except Exception as e:
        current_app.logger.error(f'خطأ في إضافة المستخدم: {str(e)}')
        db.session.rollback()
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء إضافة المستخدم'})

@bp.route('/user/<int:id>', methods=['GET'])
@login_required
def get_user(id):
    """الحصول على بيانات المستخدم"""
    if current_user.role not in ['admin', 'support']:
        return jsonify({'success': False, 'message': 'غير مصرح لك بعرض بيانات المستخدمين'})
        
    user = User.query.get_or_404(id)
    return jsonify({
        'account_number': user.account_number,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'supervisor_account': user.supervisor_account,
        'supervisor_name': user.supervisor_name
    })

@bp.route('/user/<int:id>/update', methods=['POST'])
@login_required
def update_user(id):
    """تحديث بيانات المستخدم"""
    if current_user.role not in ['admin', 'support']:
        return jsonify({'success': False, 'message': 'غير مصرح لك بتحديث بيانات المستخدمين'})
        
    user = User.query.get_or_404(id)
    
    # منع مستخدمي الدعم الفني من تعديل المستخدم المدير
    if current_user.role == 'support' and user.role == 'admin' and user.account_number == '5':
        return jsonify({'success': False, 'message': 'غير مصرح لك بتعديل بيانات هذا المستخدم'})
    
    data = request.get_json()
    
    try:
        # التحقق من عدم وجود مستخدم آخر بنفس اسم المستخدم أو البريد الإلكتروني أو رقم الحساب
        username_exists = User.query.filter(User.username == data['username'], User.id != id).first()
        if username_exists:
            return jsonify({'success': False, 'message': 'اسم المستخدم موجود بالفعل'})
        
        email_exists = User.query.filter(User.email == data['email'], User.id != id).first()
        if email_exists:
            return jsonify({'success': False, 'message': 'البريد الإلكتروني موجود بالفعل'})
        
        account_exists = User.query.filter(User.account_number == data['account_number'], User.id != id).first()
        if account_exists:
            return jsonify({'success': False, 'message': 'رقم الحساب موجود بالفعل'})
        
        # تحديث بيانات المستخدم
        user.account_number = data['account_number']
        user.username = data['username']
        user.email = data['email']
        user.role = data['role']
        user.supervisor_account = data.get('supervisor_account')
        user.supervisor_name = data.get('supervisor_name')
        
        if data.get('password'):
            user.set_password(data['password'])
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم تحديث بيانات المستخدم بنجاح'})
    except Exception as e:
        current_app.logger.error(f'خطأ في تحديث بيانات المستخدم: {str(e)}')
        db.session.rollback()
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء تحديث البيانات'})

@bp.route('/user/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    """حذف المستخدم"""
    if current_user.role not in ['admin', 'support']:
        return jsonify({'success': False, 'message': 'غير مصرح لك بحذف المستخدمين'})
        
    if id == current_user.id:
        return jsonify({'success': False, 'message': 'لا يمكنك حذف حسابك الخاص'})
    
    user = User.query.get_or_404(id)
    
    # منع مستخدمي الدعم الفني من حذف المستخدم المدير
    if current_user.role == 'support' and user.role == 'admin' and user.account_number == '5':
        return jsonify({'success': False, 'message': 'غير مصرح لك بحذف هذا المستخدم'})
    
    try:
        # التحقق من وجود شكاوى مرتبطة
        if user.complaints:
            return jsonify({'success': False, 'message': 'لا يمكن حذف المستخدم - يوجد شكاوى مرتبطة به'})
            
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف المستخدم بنجاح'})
    except Exception as e:
        current_app.logger.error(f'خطأ في حذف المستخدم: {str(e)}')
        db.session.rollback()
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء حذف المستخدم'})