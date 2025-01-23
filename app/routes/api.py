from flask import Blueprint, jsonify, request, render_template, send_file, current_app
from flask_login import login_required, current_user
from app.models import Complaint, ComplaintResponse, Notification, Service, SubService, Supervisor, Representative
from app import db
from datetime import datetime

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/complaints/stats')
@login_required
def complaints_stats():
    """إحصائيات الشكاوى"""
    # إحصائيات الشكاوى حسب الحالة
    status_stats = db.session.query(
        Complaint.status,
        db.func.count(Complaint.id)
    ).group_by(Complaint.status).all()
    
    # إحصائيات الشكاوى حسب الخدمة
    service_stats = db.session.query(
        Service.name,
        db.func.count(Complaint.id)
    ).join(Complaint).group_by(Service.id).all()
    
    return jsonify({
        'status': dict(status_stats),
        'service': dict(service_stats)
    })

@bp.route('/supervisor/<int:id>')
@login_required
def get_supervisor(id):
    """جلب بيانات مشرف"""
    try:
        supervisor = Supervisor.query.get_or_404(id)
        return jsonify({
            'success': True,
            'supervisor': {
                'id': supervisor.id,
                'name': supervisor.name,
                'account_number': supervisor.account_number,
                'representatives': [{
                    'id': rep.id,
                    'name': rep.name,
                    'account_number': rep.account_number
                } for rep in supervisor.representatives]
            }
        })
    except Exception as e:
        current_app.logger.error(f"خطأ في جلب بيانات المشرف: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء جلب بيانات المشرف'
        }), 500

@bp.route('/representative/<int:id>')
@login_required
def get_representative_api(id):
    """جلب بيانات مندوب"""
    representative = Representative.query.get_or_404(id)
    return jsonify({
        'success': True,
        'representative': {
            'id': representative.id,
            'name': representative.name,
            'account_number': representative.account_number,
            'supervisor_id': representative.supervisor_id
        }
    })

@bp.route('/service/<int:id>/sub_services')
@login_required
def get_sub_services(id):
    """جلب الخدمات الفرعية لخدمة معينة"""
    try:
        service = Service.query.get_or_404(id)
        return jsonify({
            'success': True,
            'sub_services': [{
                'id': sub.id,
                'name': sub.name
            } for sub in service.sub_services]
        })
    except Exception as e:
        current_app.logger.error(f"خطأ في جلب الخدمات الفرعية: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء جلب الخدمات الفرعية'
        }), 500

@bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    """تحديث حالة قراءة الإشعارات"""
    notification_ids = request.json.get('notification_ids', [])
    if notification_ids:
        Notification.query.filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == current_user.id
        ).update({'read': True}, synchronize_session=False)
    else:
        Notification.query.filter_by(
            user_id=current_user.id,
            read=False
        ).update({'read': True}, synchronize_session=False)
    
    db.session.commit()
    return jsonify({'message': 'تم تحديث حالة الإشعارات بنجاح'})

@bp.route('/notifications/unread')
@login_required
def get_unread_notifications():
    """جلب الإشعارات غير المقروءة"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'link': n.link,
        'created_at': n.created_at.isoformat()
    } for n in notifications])

@bp.route('/complaints/export', methods=['POST'])
@login_required
def export_complaints():
    """تصدير الشكاوى إلى ملف Excel"""
    try:
        current_app.logger.info('بدء عملية تصدير الشكاوى')
        
        # استخراج الشكاوى
        complaints = Complaint.query
        
        # تقييد الشكاوى لمستخدمي المبيعات
        if current_user.role == 'sales':
            complaints = complaints.filter_by(user_id=current_user.id)
        
        # تطبيق الفلاتر
        filters = request.get_json() or {}
        current_app.logger.info(f'الفلاتر المستخدمة: {filters}')
        
        if filters.get('merchant_account'):
            complaints = complaints.filter(
                Complaint.merchant_account.like(f'%{filters["merchant_account"]}%')
            )
        if filters.get('transaction_number'):
            complaints = complaints.filter(
                Complaint.transaction_number.like(f'%{filters["transaction_number"]}%')
            )
        if filters.get('service') and filters['service'] != '0':
            complaints = complaints.filter(Complaint.service_id == int(filters['service']))
        if filters.get('sub_service') and filters['sub_service'] != '0':
            complaints = complaints.filter(Complaint.sub_service_id == int(filters['sub_service']))
        if filters.get('status'):
            complaints = complaints.filter(Complaint.status == filters['status'])
        if filters.get('date_from'):
            complaints = complaints.filter(Complaint.created_at >= datetime.strptime(filters['date_from'], '%Y-%m-%d'))
        if filters.get('date_to'):
            complaints = complaints.filter(Complaint.created_at <= datetime.strptime(filters['date_to'], '%Y-%m-%d'))
        
        # تنفيذ الاستعلام وجلب النتائج
        complaints = complaints.all()
        current_app.logger.info(f'تم العثور على {len(complaints)} شكوى')
        
        if not complaints:
            current_app.logger.warning('لم يتم العثور على شكاوى للتصدير')
            return jsonify({
                'success': False,
                'message': 'لا توجد بيانات للتصدير'
            }), 404
        
        # تحضير البيانات للتصدير
        headers = [
            'رقم الشكوى',
            'رقم حساب المستخدم',
            'اسم المستخدم',
            'التاجر',
            'رقم العملية',
            'الخدمة',
            'الخدمة الفرعية',
            'الحالة',
            'تاريخ الإنشاء',
            'الملاحظات'
        ]
        
        data = []
        for complaint in complaints:
            try:
                status_map = {
                    'pending': 'قيد الانتظار',
                    'in_progress': 'قيد المعالجة',
                    'resolved': 'تم الحل',
                    'rejected': 'مرفوضة'
                }
                
                row = [
                    str(complaint.id),
                    complaint.user.account_number,
                    complaint.user.username,
                    complaint.merchant_account,
                    complaint.transaction_number,
                    complaint.service.name,
                    complaint.sub_service.name,
                    status_map.get(complaint.status, complaint.status),
                    complaint.created_at.strftime('%Y-%m-%d %H:%M'),
                    complaint.notes or ''
                ]
                data.append(row)
                current_app.logger.debug(f'تمت معالجة الشكوى {complaint.id} بنجاح')
            except Exception as row_error:
                current_app.logger.error(f'خطأ في معالجة الشكوى {complaint.id}: {str(row_error)}')
        
        current_app.logger.info(f'تم تحضير {len(data)} صف من البيانات للتصدير')
        
        try:
            # إنشاء ملف Excel
            current_app.logger.info('بدء إنشاء ملف Excel...')
            from app.utils.export import generate_excel
            output = generate_excel(headers, data)
            current_app.logger.info('تم إنشاء ملف Excel بنجاح')
            
            response = send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'complaints_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
            response.headers.set('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response.headers.set('Content-Disposition', 'attachment; filename=complaints.xlsx')
            current_app.logger.info('تم إرسال ملف Excel بنجاح')
            return response
                
        except Exception as export_error:
            current_app.logger.error(f'خطأ في إنشاء الملف: {str(export_error)}')
            raise
        
    except Exception as e:
        current_app.logger.error(f'خطأ في تصدير الشكاوى: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تصدير الشكاوى'
        }), 500 