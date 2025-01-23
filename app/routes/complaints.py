from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app.models import Complaint, ComplaintResponse, Service, SubService, Supervisor, Representative, User
from app.forms import ComplaintForm, ComplaintResponseForm, ComplaintSearchForm
from app.utils import save_file, delete_file, send_notification, send_email
from app.utils.decorators import sales_required
from app import db
from datetime import datetime
import os
import io
import xlsxwriter

bp = Blueprint('complaints', __name__, url_prefix='/complaints')

@bp.route('/uploads/<path:filename>')
@login_required
def uploads(filename):
    """عرض الملفات المرفقة"""
    try:
        return send_file(
            os.path.join(current_app.config['UPLOAD_FOLDER'], filename),
            as_attachment=False
        )
    except Exception as e:
        current_app.logger.error(f'خطأ في عرض الملف: {str(e)}')
        flash('لا يمكن عرض الملف المطلوب', 'error')
        return redirect(url_for('complaints.index'))

@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """عرض قائمة الشكاوى"""
    form = ComplaintSearchForm()
    
    # تحميل الخيارات
    services = Service.query.all()
    form.service.choices = [(0, 'اختر الخدمة')] + [(s.id, s.name) for s in services]
    form.sub_service.choices = [(0, 'اختر الخدمة الفرعية')]
    
    # الاستعلام الأساسي
    query = Complaint.query.join(Complaint.user)
    
    # تصفية حسب دور المستخدم
    if current_user.role == 'sales':
        query = query.filter(Complaint.user_id == current_user.id)
    
    # تطبيق معايير البحث
    if form.validate_on_submit():
        if form.supervisor_account.data:
            query = query.filter(User.supervisor_account == form.supervisor_account.data)
        if form.user_account.data:
            query = query.filter(User.account_number == form.user_account.data)
        if form.merchant_account.data:
            query = query.filter(Complaint.merchant_account.ilike(f'%{form.merchant_account.data}%'))
        if form.transaction_number.data:
            query = query.filter(Complaint.transaction_number.ilike(f'%{form.transaction_number.data}%'))
        if form.service.data and form.service.data != 0:
            query = query.filter_by(service_id=form.service.data)
        if form.sub_service.data and form.sub_service.data != 0:
            query = query.filter_by(sub_service_id=form.sub_service.data)
        if form.status.data:
            query = query.filter_by(status=form.status.data)
        if form.date_from.data:
            query = query.filter(Complaint.created_at >= form.date_from.data)
        if form.date_to.data:
            query = query.filter(Complaint.created_at <= form.date_to.data)
    
    page = request.args.get('page', 1, type=int)
    
    # جلب الشكاوى مع الترقيم
    complaints = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=10)
    
    # قاموس ألوان الحالات
    status_colors = {
        'pending': 'warning',
        'in_progress': 'info',
        'resolved': 'success',
        'rejected': 'danger'
    }
    
    # قاموس تسميات الحالات
    status_labels = {
        'pending': 'قيد الانتظار',
        'in_progress': 'قيد المعالجة',
        'resolved': 'تم الحل',
        'rejected': 'مرفوضة'
    }
    
    return render_template('complaints/index.html', 
                         complaints=complaints, 
                         form=form,
                         status_colors=status_colors,
                         status_labels=status_labels)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@sales_required
def create():
    """إنشاء شكوى جديدة"""
    current_app.logger.debug('=== بدء طلب إنشاء شكوى جديدة ===')
    current_app.logger.debug(f'طريقة الطلب: {request.method}')
    if request.method == 'POST':
        current_app.logger.debug('=== بيانات النموذج المرسلة ===')
        current_app.logger.debug(f'النموذج: {request.form}')
        current_app.logger.debug(f'الملفات: {request.files}')
        current_app.logger.debug(f'الرؤوس: {request.headers}')
    
    form = ComplaintForm()
    
    try:
        current_app.logger.debug('=== بدء عملية إنشاء شكوى جديدة ===')
        current_app.logger.debug(f'المستخدم الحالي: {current_user.username} (ID: {current_user.id})')
        
        services = Service.query.all()
        current_app.logger.debug(f'تم تحميل {len(services)} خدمة')
        
        form.service.choices = [(0, 'اختر الخدمة')] + [
            (s.id, s.name) for s in services
        ]
        
        # تحميل الخدمات الفرعية إذا تم اختيار خدمة
        if form.service.data and form.service.data != 0:
            service = Service.query.get(form.service.data)
            if service:
                current_app.logger.debug(f'تم تحميل {len(service.sub_services)} خدمة فرعية للخدمة {service.name}')
                form.sub_service.choices = [(0, 'اختر الخدمة الفرعية')] + [
                    (s.id, s.name) for s in service.sub_services
                ]
        else:
            form.sub_service.choices = [(0, 'اختر الخدمة الفرعية')]
        
        if form.validate_on_submit():
            current_app.logger.debug('=== بدء التحقق من صحة النموذج ===')
            current_app.logger.debug('البيانات المرسلة:')
            current_app.logger.debug(f'رقم التاجر: {form.merchant_account.data}')
            current_app.logger.debug(f'الخدمة: {form.service.data}')
            current_app.logger.debug(f'الخدمة الفرعية: {form.sub_service.data}')
            current_app.logger.debug(f'رقم العملية: {form.transaction_number.data}')
            current_app.logger.debug(f'الملاحظات: {form.notes.data}')

            # التحقق من عدم تكرار رقم العملية في النظام
            existing_complaint = Complaint.query.filter_by(
                transaction_number=form.transaction_number.data
            ).first()
            if existing_complaint:
                current_app.logger.warning(f'محاولة إنشاء شكوى برقم عملية مكرر: {form.transaction_number.data}')
                form.transaction_number.errors = ['رقم العملية مستخدم بالفعل في شكوى أخرى في النظام']
                return render_template('complaints/create.html', form=form)

            if form.service.data == 0:
                current_app.logger.warning('لم يتم اختيار الخدمة')
                flash('يرجى اختيار الخدمة', 'error')
                return render_template('complaints/create.html', form=form)
            
            if form.sub_service.data == 0:
                current_app.logger.warning('لم يتم اختيار الخدمة الفرعية')
                flash('يرجى اختيار الخدمة الفرعية', 'error')
                return render_template('complaints/create.html', form=form)
            
            # حفظ المرفق إذا وجد
            attachment = None
            try:
                if form.attachment.data:
                    current_app.logger.debug('=== بدء حفظ المرفق ===')
                    current_app.logger.debug(f'اسم الملف: {form.attachment.data.filename}')
                    current_app.logger.debug(f'نوع الملف: {form.attachment.data.content_type}')
                    
                    # التحقق من وجود الملف
                    if not form.attachment.data.filename:
                        current_app.logger.error('لم يتم اختيار ملف')
                        flash('يرجى اختيار ملف صالح', 'error')
                        return render_template('complaints/create.html', form=form)
                    
                    # حفظ الملف
                    attachment = save_file(form.attachment.data, 'complaints')
                    current_app.logger.debug(f'نتيجة حفظ المرفق: {attachment}')
                    
                    if not attachment:
                        current_app.logger.error('فشل في حفظ المرفق')
                        flash('حدث خطأ أثناء حفظ المرفق', 'error')
                        return render_template('complaints/create.html', form=form)
                    
                    # التحقق من وجود الملف بعد الحفظ
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment)
                    if not os.path.exists(file_path):
                        current_app.logger.error(f'الملف غير موجود بعد الحفظ: {file_path}')
                        flash('حدث خطأ أثناء حفظ المرفق', 'error')
                        return render_template('complaints/create.html', form=form)
                
                # إنشاء الشكوى
                complaint = Complaint(
                    user_id=current_user.id,
                    supervisor_id=None,  # تعيين قيمة فارغة للمشرف
                    representative_id=None,  # تعيين قيمة فارغة للمندوب
                    service_id=form.service.data,
                    sub_service_id=form.sub_service.data,
                    merchant_account=form.merchant_account.data,
                    transaction_number=form.transaction_number.data,
                    notes=form.notes.data,
                    attachment=attachment,
                    status='pending'
                )
                
                current_app.logger.debug('محاولة حفظ الشكوى في قاعدة البيانات')
                db.session.add(complaint)
                db.session.commit()
                current_app.logger.info(f'تم حفظ الشكوى بنجاح. معرف الشكوى: {complaint.id}')
                
                # إرسال إشعارات للمدير والدعم الفني
                current_app.logger.debug('إرسال إشعارات للمدير والدعم الفني')
                admin_users = User.query.filter(User.role.in_(['admin', 'support'])).all()
                for user in admin_users:
                    send_notification(
                        user,
                        'شكوى جديدة',
                        f'تم إضافة شكوى جديدة برقم {complaint.id}',
                        'info',
                        url_for('complaints.view', id=complaint.id)
                    )
                
                flash('تم إنشاء الشكوى بنجاح', 'success')
                return redirect(url_for('complaints.view', id=complaint.id))
            
            except Exception as e:
                # حذف المرفق إذا تم حفظه ولكن فشل حفظ الشكوى
                if attachment:
                    delete_file(attachment)
                
                db.session.rollback()
                current_app.logger.error(f'خطأ في حفظ الشكوى: {str(e)}')
                flash('حدث خطأ أثناء حفظ الشكوى', 'error')
                return render_template('complaints/create.html', form=form)
    
    except Exception as e:
        current_app.logger.error(f'خطأ في صفحة إنشاء الشكوى: {str(e)}')
        flash('حدث خطأ أثناء تحميل الصفحة', 'error')
    
    return render_template('complaints/create.html', form=form)

@bp.route('/<int:id>')
@login_required
def view(id):
    try:
        # تحميل الشكوى مع جميع العلاقات
        query = Complaint.query.options(
            db.joinedload(Complaint.supervisor),
            db.joinedload(Complaint.representative),
            db.joinedload(Complaint.service),
            db.joinedload(Complaint.sub_service),
            db.joinedload(Complaint.user),
            db.joinedload(Complaint.responses).joinedload(ComplaintResponse.user)
        )
        
        # تقييد الشكاوى حسب صلاحيات المستخدم
        if current_user.role == 'sales':
            complaint = query.filter_by(id=id, user_id=current_user.id).first_or_404()
        else:
            complaint = query.filter_by(id=id).first_or_404()
        
        form = ComplaintResponseForm()
        
        # حساب الوقت المنقضي
        waiting_time = datetime.now() - complaint.created_at
        waiting_hours = waiting_time.total_seconds() / 3600
        
        # تحديد لون الحالة
        status_colors = {
            'pending': 'warning',
            'in_progress': 'info',
            'resolved': 'success',
            'rejected': 'danger'
        }
        
        # تسميات الحالات
        status_labels = {
            'pending': 'قيد الانتظار',
            'in_progress': 'قيد المعالجة',
            'resolved': 'تم الحل',
            'rejected': 'مرفوضة'
        }
        
        # حساب آخر تحديث
        last_update = datetime.now() - complaint.updated_at
        last_update_hours = last_update.total_seconds() / 3600
        
        # تنسيق الوقت
        if waiting_hours < 24:
            waiting_time = f'{int(waiting_hours)} ساعة'
        else:
            waiting_time = f'{int(waiting_hours/24)} يوم'
        
        if last_update_hours < 24:
            last_update = f'{int(last_update_hours)} ساعة'
        else:
            last_update = f'{int(last_update_hours/24)} يوم'
        
        return render_template('complaints/view.html',
                            complaint=complaint,
                            form=form,
                            waiting_time=waiting_time,
                            last_update=last_update,
                            status_colors=status_colors,
                            status_labels=status_labels)
                            
    except Exception as e:
        current_app.logger.error(f'خطأ في صفحة عرض تفاصيل الشكوى: {str(e)}')
        flash('حدث خطأ أثناء تحميل تفاصيل الشكوى', 'error')
        return redirect(url_for('complaints.index'))

@bp.route('/<int:id>/response', methods=['POST'])
@login_required
def add_response(id):
    # تعديل الاستعلام ليشمل فلتر المستخدم للمبيعات
    if current_user.role == 'sales':
        complaint = Complaint.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    else:
        complaint = Complaint.query.get_or_404(id)
        
    form = ComplaintResponseForm()
    
    try:
        current_app.logger.debug('=== بدء إضافة رد جديد ===')
        current_app.logger.debug(f'معرف الشكوى: {id}')
        current_app.logger.debug(f'المستخدم: {current_user.username} (الدور: {current_user.role})')
        
        if form.validate_on_submit():
            # حفظ المرفق إذا وجد
            attachment = None
            if form.attachment.data:
                current_app.logger.debug('محاولة حفظ المرفق')
                attachment = save_file(form.attachment.data, 'responses')
                if not attachment:
                    current_app.logger.error('فشل في حفظ المرفق')
                    flash('حدث خطأ أثناء حفظ المرفق', 'error')
                    return redirect(url_for('complaints.view', id=id))
            
            # إضافة الرد
            response = ComplaintResponse(
                complaint_id=complaint.id,
                user_id=current_user.id,
                response=form.response.data,
                attachment=attachment
            )
            db.session.add(response)
            
            # تحديث حالة الشكوى فقط للمدير والدعم الفني
            if current_user.role in ['admin', 'support'] and hasattr(form, 'status'):
                current_app.logger.debug(f'تحديث حالة الشكوى إلى: {form.status.data}')
                complaint.status = form.status.data
            
            db.session.commit()
            current_app.logger.info('تم حفظ الرد بنجاح')
            
            # إرسال إشعارات
            # إشعار لصاحب الشكوى إذا كان الرد من غيره
            if complaint.user_id != current_user.id:
                current_app.logger.debug('إرسال إشعار لصاحب الشكوى')
                send_notification(
                    complaint.user,
                    'رد جديد على الشكوى',
                    f'تم إضافة رد جديد على الشكوى رقم {complaint.id}',
                    'info',
                    url_for('complaints.view', id=complaint.id)
                )
            
            # إشعار للمدير والدعم الفني إذا كان الرد من المبيعات
            if current_user.role == 'sales':
                current_app.logger.debug('إرسال إشعارات للمدير والدعم الفني')
                admin_users = User.query.filter(User.role.in_(['admin', 'support'])).all()
                for user in admin_users:
                    send_notification(
                        user,
                        'رد جديد من المبيعات',
                        f'تم إضافة رد جديد من المبيعات على الشكوى رقم {complaint.id}',
                        'info',
                        url_for('complaints.view', id=complaint.id)
                    )
            
            flash('تم إضافة الرد بنجاح', 'success')
            return redirect(url_for('complaints.view', id=complaint.id))
        
        current_app.logger.debug('أخطاء التحقق:')
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.debug(f'{field}: {error}')
                flash(f'{getattr(form, field).label.text}: {error}', 'error')
        
        return redirect(url_for('complaints.view', id=complaint.id))
    
    except Exception as e:
        current_app.logger.error(f'خطأ في إضافة الرد: {str(e)}')
        flash('حدث خطأ أثناء إضافة الرد', 'error')
        return redirect(url_for('complaints.view', id=complaint.id))

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    complaint = Complaint.query.get_or_404(id)
    
    # التحقق من الصلاحيات
    if current_user.role not in ['admin', 'support']:
        return jsonify({'error': 'غير مصرح لك بحذف هذه الشكوى'}), 403
    
    # حذف المرفقات
    if complaint.attachment:
        delete_file(complaint.attachment)
    
    for response in complaint.responses:
        if response.attachment:
            delete_file(response.attachment)
    
    db.session.delete(complaint)
    db.session.commit()
    
    flash('تم حذف الشكوى بنجاح', 'success')
    return jsonify({'success': True})

@bp.route('/response/<int:id>/delete', methods=['POST'])
@login_required
def delete_response(id):
    # البحث عن الرد مع التحقق من الصلاحيات
    if current_user.role == 'sales':
        response = ComplaintResponse.query.join(Complaint).filter(
            ComplaintResponse.id == id,
            Complaint.user_id == current_user.id
        ).first_or_404()
    else:
        response = ComplaintResponse.query.get_or_404(id)
    
    # حذف المرفق
    if response.attachment:
        delete_file(response.attachment)
    
    db.session.delete(response)
    db.session.commit()
    
    flash('تم حذف الرد بنجاح', 'success')
    return jsonify({'success': True})

@bp.route('/download', methods=['GET', 'POST'])
@login_required
def download_complaints():
    """تنزيل الشكاوى المعروضة في شكل Excel"""
    try:
        # الاستعلام الأساسي
        query = Complaint.query.join(Complaint.user).join(Complaint.service).join(Complaint.sub_service)
        
        # تصفية حسب دور المستخدم
        if current_user.role == 'sales':
            query = query.filter(Complaint.user_id == current_user.id)
        
        # تطبيق معايير البحث من النموذج أو الـ query parameters
        if request.method == 'POST':
            form_data = request.get_json()
        else:
            form_data = request.args
        
        current_app.logger.debug(f'بيانات البحث المستلمة: {form_data}')
        
        if form_data:
            if form_data.get('supervisor_account'):
                query = query.filter(User.supervisor_account == form_data.get('supervisor_account'))
            if form_data.get('user_account'):
                query = query.filter(User.account_number == form_data.get('user_account'))
            if form_data.get('merchant_account'):
                query = query.filter(Complaint.merchant_account.ilike(f'%{form_data.get("merchant_account")}%'))
            if form_data.get('transaction_number'):
                query = query.filter(Complaint.transaction_number.ilike(f'%{form_data.get("transaction_number")}%'))
            if form_data.get('service') and str(form_data.get('service')) != '0':
                query = query.filter(Complaint.service_id == int(form_data.get('service')))
            if form_data.get('sub_service') and str(form_data.get('sub_service')) != '0':
                query = query.filter(Complaint.sub_service_id == int(form_data.get('sub_service')))
            if form_data.get('status'):
                query = query.filter(Complaint.status == form_data.get('status'))
            if form_data.get('date_from'):
                date_from = datetime.strptime(form_data.get('date_from'), '%Y-%m-%d')
                query = query.filter(Complaint.created_at >= date_from)
            if form_data.get('date_to'):
                date_to = datetime.strptime(form_data.get('date_to'), '%Y-%m-%d')
                query = query.filter(Complaint.created_at <= date_to)
        
        # تنفيذ الاستعلام
        complaints = query.order_by(Complaint.created_at.desc()).all()
        
        current_app.logger.debug(f'تم العثور على {len(complaints)} شكوى للتصدير')
        
        if not complaints:
            flash('لا توجد شكاوى للتصدير', 'warning')
            return redirect(url_for('complaints.index'))
        
        # إنشاء ملف Excel في الذاكرة
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('الشكاوى')
        
        # تنسيق العناوين
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4CAF50',
            'font_color': 'white',
            'border': 1,
            'font_size': 12,
            'font_name': 'Arial'
        })
        
        # تنسيق البيانات
        data_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 10,
            'font_name': 'Arial'
        })
        
        # كتابة العناوين
        headers = [
            'رقم الشكوى',
            'رقم حساب المستخدم',
            'اسم المستخدم',
            'رقم حساب المشرف',
            'اسم المشرف',
            'رقم حساب التاجر',
            'رقم العملية',
            'الخدمة',
            'الخدمة الفرعية',
            'الحالة',
            'تاريخ الإنشاء',
            'الملاحظات'
        ]
        
        # تعيين عرض الأعمدة
        column_widths = [10, 15, 20, 15, 20, 15, 15, 20, 20, 15, 20, 40]
        for col, width in enumerate(column_widths):
            worksheet.set_column(col, col, width)
        
        # كتابة العناوين
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # كتابة البيانات
        status_labels = {
            'pending': 'قيد الانتظار',
            'in_progress': 'قيد المعالجة',
            'resolved': 'تم الحل',
            'rejected': 'مرفوضة'
        }
        
        for row, complaint in enumerate(complaints, start=1):
            data = [
                complaint.id,
                complaint.user.account_number,
                complaint.user.username,
                complaint.user.supervisor_account or '-',
                complaint.user.supervisor_name or '-',
                complaint.merchant_account,
                complaint.transaction_number,
                complaint.service.name,
                complaint.sub_service.name,
                status_labels.get(complaint.status, complaint.status),
                complaint.created_at.strftime('%Y-%m-%d %H:%M'),
                complaint.notes
            ]
            for col, value in enumerate(data):
                worksheet.write(row, col, value, data_format)
        
        workbook.close()
        output.seek(0)
        
        # إرسال الملف
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'complaints_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        current_app.logger.error(f'خطأ في تصدير الشكاوى: {str(e)}')
        flash('حدث خطأ أثناء تصدير الشكاوى', 'error')
        return redirect(url_for('complaints.index')) 