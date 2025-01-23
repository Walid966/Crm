from flask import Blueprint, app, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from app.models import Supervisor, Representative, Service, SubService, Complaint
from app.forms import SupervisorForm, ServiceForm
from app.utils.decorators import admin_required
from app import db
import pandas as pd
from werkzeug.utils import secure_filename
import os
import tempfile
import xlsxwriter

bp = Blueprint('management', __name__, url_prefix='/management')

@bp.route('/')
@login_required
@admin_required
def index():
    """صفحة الإدارة"""
    # جلب جميع المشرفين والخدمات
    supervisors = Supervisor.query.all()
    services = Service.query.all()
    
    current_app.logger.info("تم تحميل صفحة الإدارة")
    current_app.logger.info(f"عدد المشرفين: {len(supervisors)}")
    current_app.logger.info(f"عدد الخدمات: {len(services)}")
    
    return render_template('management/index.html', 
                         supervisors=supervisors,
                         services=services)

@bp.route('/supervisor/add', methods=['POST'])
@login_required
@admin_required
def add_supervisor():
    """إضافة مشرف جديد"""
    if not request.is_json:
        return jsonify({
            'success': False,
            'message': 'يجب إرسال البيانات بتنسيق JSON'
        }), 400

    data = request.get_json()
    
    # التحقق من البيانات لمطلوبة
    if not all(key in data for key in ['account_number', 'name', 'representatives']):
        return jsonify({
            'success': False,
            'message': 'البيانات غير مكتملة'
        }), 400
    
    try:
        # التحقق من عدم وجود المشرف
        if Supervisor.query.filter_by(account_number=data['account_number']).first():
            return jsonify({
                'success': False,
                'message': 'رقم حساب المشرف مستخدم بالفعل'
            }), 400
        
        # التحقق من عدم وجود المناديب
        rep_account_numbers = [rep['account_number'] for rep in data['representatives']]
        if len(rep_account_numbers) != len(set(rep_account_numbers)):
            return jsonify({
                'success': False,
                'message': 'لا يمكن تكرار رقم حساب المندوب'
            }), 400
        
        existing_reps = Representative.query.filter(
            Representative.account_number.in_(rep_account_numbers)
        ).all()
        if existing_reps:
            return jsonify({
                'success': False,
                'message': f'رقم حساب المندوب {existing_reps[0].account_number} مستخدم بالفعل'
            }), 400
        
        # إنشاء المشرف
        supervisor = Supervisor(
            account_number=data['account_number'],
            name=data['name']
        )
        db.session.add(supervisor)
        
        # إنشاء المناديب
        for rep_data in data['representatives']:
            representative = Representative(
                account_number=rep_data['account_number'],
                name=rep_data['name'],
                supervisor=supervisor
            )
            db.session.add(representative)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم إضافة المشرف والمناديب بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إضافة المشرف والمناديب'
        }), 500

@bp.route('/api/supervisor/<int:id>')
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

@bp.route('/supervisor/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_supervisor(id):
    """تحديث مشرف"""
    if not request.is_json:
        return jsonify({
            'success': False,
            'message': 'يجب إرسال البيانات بتنسيق JSON'
        }), 400

    supervisor = Supervisor.query.get_or_404(id)
    data = request.get_json()
    
    # التحقق من البيانات المطلوبة
    if not all(key in data for key in ['account_number', 'name', 'representatives']):
        return jsonify({
            'success': False,
            'message': 'البيانات غير مكتملة'
        }), 400
    
    try:
        # التحقق من عدم وجود المشرف بنفس رقم الحساب
        existing_supervisor = Supervisor.query.filter(
            Supervisor.account_number == data['account_number'],
            Supervisor.id != id
        ).first()
        if existing_supervisor:
            return jsonify({
                'success': False,
                'message': 'رقم حساب المشرف مستخدم بالفعل'
            }), 400
        
        # التحقق من عدم وجود المناديب
        rep_account_numbers = [rep['account_number'] for rep in data['representatives']]
        if len(rep_account_numbers) != len(set(rep_account_numbers)):
            return jsonify({
                'success': False,
                'message': 'لا يمكن تكرار رقم حساب المندوب'
            }), 400
        
        existing_reps = Representative.query.filter(
            Representative.account_number.in_(rep_account_numbers),
            Representative.supervisor_id != id
        ).all()
        if existing_reps:
            return jsonify({
                'success': False,
                'message': f'رقم حساب المندوب {existing_reps[0].account_number} مستخدم بالفعل'
            }), 400
        
        # تحديث بيانات المشرف
        supervisor.account_number = data['account_number']
        supervisor.name = data['name']
        
        # حذف المناديب القديمين
        Representative.query.filter_by(supervisor_id=id).delete()
        
        # إضافة المناديب الجدد
        for rep_data in data['representatives']:
            representative = Representative(
                account_number=rep_data['account_number'],
                name=rep_data['name'],
                supervisor=supervisor
            )
            db.session.add(representative)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم تحديث المشرف والمناديب بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تحديث المشرف والمناديب'
        }), 500

@bp.route('/supervisor/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_supervisor(id):
    """حذف مشرف"""
    try:
        current_app.logger.info(f"بدء عملية حذف المشرف {id}")
        
        # التحقق من وجود المشرف
        supervisor = Supervisor.query.get_or_404(id)
        current_app.logger.info(f"تم العثور على المشرف: {supervisor.name} ({supervisor.account_number})")
        
        # التحقق من وجود شكاوى مرتبطة
        complaints = Complaint.query.filter(
            (Complaint.supervisor_id == supervisor.id) |
            (Complaint.representative_id.in_([r.id for r in supervisor.representatives]))
        ).all()
        
        if complaints:
            error_msg = f"لا يمكن حذف المشرف {supervisor.name} - يوجد {len(complaints)} شكوى مرتبطة به أو بمناديبه"
            current_app.logger.warning(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400
        
        # حذف المناديب أولاً
        Representative.query.filter_by(supervisor_id=id).delete()
        
        # حذف المشرف
        db.session.delete(supervisor)
        db.session.commit()
        
        current_app.logger.info(f"تم حذف المشرف {supervisor.name} ومناديبه بنجاح")
        return jsonify({
            'success': True,
            'message': 'تم حذف المشرف ومناديبه بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"خطأ في حذف المشرف: {str(e)}"
        current_app.logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف المشرف'
        }), 500

@bp.route('/service/add', methods=['POST'])
@login_required
@admin_required
def add_service():
    """إضافة خدمة جديدة"""
    if not request.is_json:
        return jsonify({
            'success': False,
            'message': 'يجب إرسال البيانات بتنسيق JSON'
        }), 400

    data = request.get_json()
    
    # التحقق من البيانات المطلوبة
    if not all(key in data for key in ['name', 'sub_services']):
        return jsonify({
            'success': False,
            'message': 'البيانات غير مكتملة'
        }), 400
    
    try:
        # التحقق من عدم وجود الخدمة
        if Service.query.filter_by(name=data['name']).first():
            return jsonify({
                'success': False,
                'message': 'اسم الخدمة مستخدم بالفعل'
            }), 400
        
        # إنشاء الخدمة
        service = Service(name=data['name'])
        db.session.add(service)
        
        # إنشاء الخدمات الفرعية
        for sub_service_data in data['sub_services']:
            sub_service = SubService(
                name=sub_service_data['name'],
                service=service
            )
            db.session.add(sub_service)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم إضافة الخدمة بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إضافة الخدمة'
        }), 500

@bp.route('/service/<int:id>/get')
@login_required
@admin_required
def get_service(id):
    """جلب بيانات خدمة"""
    service = Service.query.get_or_404(id)
    return jsonify({
        'success': True,
        'service': {
            'id': service.id,
            'name': service.name,
            'sub_services': [{
                'id': sub.id,
                'name': sub.name
            } for sub in service.sub_services]
        }
    })

@bp.route('/service/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_service(id):
    """تحديث خدمة"""
    if not request.is_json:
        return jsonify({
            'success': False,
            'message': 'يجب إرسال البيانات بتنسيق JSON'
        }), 400

    service = Service.query.get_or_404(id)
    data = request.get_json()
    
    # التحقق من البيانات المطلوبة
    if not all(key in data for key in ['name', 'sub_services']):
        return jsonify({
            'success': False,
            'message': 'البيانات غير مكتملة'
        }), 400
    
    try:
        # التحقق من عدم وجود الخدمة بنفس الاسم
        existing_service = Service.query.filter(
            Service.name == data['name'],
            Service.id != id
        ).first()
        if existing_service:
            return jsonify({
                'success': False,
                'message': 'اسم الخدمة مستخدم بالفعل'
            }), 400
        
        # الحصول على الخدمات الفرعية الحالية
        current_sub_services = {sub.name: sub for sub in service.sub_services}
        new_sub_services = {sub['name']: None for sub in data['sub_services']}
        
        # التحقق من الخدمات الفرعية التي سيتم حذفها
        sub_services_to_delete = set(current_sub_services.keys()) - set(new_sub_services.keys())
        for sub_name in sub_services_to_delete:
            sub_service = current_sub_services[sub_name]
            # التحقق من وجود شكاوى مرتبطة
            if Complaint.query.filter_by(sub_service_id=sub_service.id).first():
                return jsonify({
                    'success': False,
                    'message': f'لا يمكن حذف الخدمة الفرعية "{sub_name}" - يوجد شكاوى مرتبطة بها'
                }), 400
        
        # تحديث بيانات الخدمة
        service.name = data['name']
        
        # تحديث الخدمات الفرعية
        # الاحتفاظ بالخدمات الفرعية الموجودة في القائمة الجديدة
        kept_sub_services = set(current_sub_services.keys()) & set(new_sub_services.keys())
        
        # حذف الخدمات الفرعية غير الموجودة في القائمة الجديدة
        for sub_name in sub_services_to_delete:
            db.session.delete(current_sub_services[sub_name])
        
        # إضافة الخدمات الفرعية الجديدة
        for sub_data in data['sub_services']:
            if sub_data['name'] not in kept_sub_services:
                sub_service = SubService(
                    name=sub_data['name'],
                    service=service
                )
                db.session.add(sub_service)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم تحديث الخدمة والخدمات الفرعية بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في تحديث الخدمة: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تحديث الخدمة والخدمات الفرعية'
        }), 500

@bp.route('/service/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_service(id):
    """حذف خدمة"""
    try:
        service = Service.query.get_or_404(id)
        
        # التحقق من وجود شكاوى مرتبطة
        complaints = Complaint.query.filter_by(service_id=id).first()
        if complaints:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف الخدمة - يوجد شكاوى مرتبطة بها'
            }), 400
            
        # حذف الخدمات الفرعية أولاً
        SubService.query.filter_by(service_id=id).delete()
        
        # حذف الخدمة
        db.session.delete(service)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف الخدمة وخدماتها الفرعية بنجاح'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في حذف الخدمة: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء حذف الخدمة'
        }), 500

@bp.route('/api/representatives/<supervisor_id>')
@login_required
@admin_required
def get_representatives(supervisor_id):
    """إرجاع مناديب مشرف"""
    representatives = Representative.query.filter_by(supervisor_id=supervisor_id).all()
    return jsonify([{
        'id': rep.id,
        'account_number': rep.account_number,
        'name': rep.name
    } for rep in representatives])

@bp.route('/api/sub-services/<service_id>')
@login_required
@admin_required
def get_sub_services(service_id):
    """إرجاع الخدمات الفرعية"""
    sub_services = SubService.query.filter_by(service_id=service_id).all()
    return jsonify([{
        'id': sub.id,
        'name': sub.name
    } for sub in sub_services])

@bp.route('/supervisors/import', methods=['POST'])
@login_required
@admin_required
def import_supervisors():
    """استيراد المشرفين من ملف Excel"""
    try:
        current_app.logger.info("بدء عملية استيراد المشرفين")
        
        if 'file' not in request.files:
            current_app.logger.error("لم يتم تقديم ملف")
            return jsonify({
                'success': False,
                'message': 'يرجى اختيار ملف'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            current_app.logger.error("لم يتم اختيار ملف")
            return jsonify({
                'success': False,
                'message': 'يرجى اختيار ملف'
            }), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            current_app.logger.error("نوع الملف غير مدعوم")
            return jsonify({
                'success': False,
                'message': 'يجب أن يكون الملف بصيغة Excel (.xlsx, .xls)'
            }), 400
        
        # قراءة الملف
        current_app.logger.info("قراءة الملف...")
        df = pd.read_excel(file)
        current_app.logger.info(f"تم قراءة {len(df)} صف من البيانات")
        
        # التحقق من الأعمدة المطلوبة
        required_columns = ['رقم حساب المشرف', 'اسم المشرف', 'رقم حساب المندوب', 'اسم المندوب']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            current_app.logger.error(f"أعمدة مفقودة: {missing_columns}")
            return jsonify({
                'success': False,
                'message': f'الأعمدة التالية مفقودة: {", ".join(missing_columns)}'
            }), 400
        
        # تجميع البيانات
        supervisors_data = {}
        for index, row in df.iterrows():
            try:
                supervisor_account = str(row['رقم حساب المشرف']).strip()
                supervisor_name = str(row['اسم المشرف']).strip()
                representative_account = str(row['رقم حساب المندوب']).strip()
                representative_name = str(row['اسم المندوب']).strip()
                
                if not all([supervisor_account, supervisor_name, representative_account, representative_name]):
                    current_app.logger.error(f"بيانات غير مكتملة في الصف {index + 2}")
                    continue
                
                if supervisor_account not in supervisors_data:
                    supervisors_data[supervisor_account] = {
                        'name': supervisor_name,
                        'representatives': []
                    }
                
                # التحقق من عدم تكرار المندوب
                if not any(rep['account_number'] == representative_account 
                         for rep in supervisors_data[supervisor_account]['representatives']):
                    supervisors_data[supervisor_account]['representatives'].append({
                        'account_number': representative_account,
                        'name': representative_name
                    })
            
            except Exception as e:
                current_app.logger.error(f"خطأ في معالجة الصف {index + 2}: {str(e)}")
                continue
        
        if not supervisors_data:
            current_app.logger.error("لم يتم العثور على بيانات صالحة")
            return jsonify({
                'success': False,
                'message': 'لم يتم العثور على بيانات صالحة في الملف'
            }), 400
        
        # حفظ البيانات
        current_app.logger.info("حفظ البيانات...")
        for supervisor_account, data in supervisors_data.items():
            try:
                # البحث عن المشرف أو إنشاء واحد جديد
                supervisor = Supervisor.query.filter_by(account_number=supervisor_account).first()
                if supervisor:
                    supervisor.name = data['name']
                    current_app.logger.info(f"تحديث المشرف: {supervisor.name}")
                else:
                    supervisor = Supervisor(
                        account_number=supervisor_account,
                        name=data['name']
                    )
                    db.session.add(supervisor)
                    current_app.logger.info(f"إضافة مشرف جديد: {supervisor.name}")
                
                db.session.flush()  # للحصول على معرف المشرف
                
                # معالجة المناديب
                for rep_data in data['representatives']:
                    representative = Representative.query.filter_by(
                        account_number=rep_data['account_number']
                    ).first()
                    
                    if representative:
                        if representative.supervisor_id != supervisor.id:
                            current_app.logger.error(
                                f"المندوب {representative.name} مرتبط بمشرف آخر"
                            )
                            db.session.rollback()
                            return jsonify({
                                'success': False,
                                'message': f'المندوب {representative.name} مرتبط بمشرف آخر'
                            }), 400
                        representative.name = rep_data['name']
                        current_app.logger.info(f"تحديث المندوب: {representative.name}")
                    else:
                        representative = Representative(
                            account_number=rep_data['account_number'],
                            name=rep_data['name'],
                            supervisor_id=supervisor.id
                        )
                        db.session.add(representative)
                        current_app.logger.info(f"إضافة مندوب جديد: {representative.name}")
            
            except Exception as e:
                current_app.logger.error(f"خطأ في معالجة المشرف {supervisor_account}: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'خطأ في معالجة المشرف {supervisor_account}'
                }), 500
        
        db.session.commit()
        current_app.logger.info("تم الاستيراد بنجاح")
        return jsonify({
            'success': True,
            'message': 'تم استيراد البيانات بنجاح'
        })
        
    except Exception as e:
        current_app.logger.error(f"خطأ في استيراد البيانات: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء استيراد البيانات'
        }), 500

@bp.route('/services/import', methods=['POST'])
@login_required
@admin_required
def import_services():
    """استيراد الخدمات من ملف Excel"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'لم يتم تحديد ملف'
            }), 400
        
        file = request.files['file']
        if not file or not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({
                'success': False,
                'message': 'يجب تحديد ملف Excel صالح'
            }), 400
        
        # قراءة الملف
        df = pd.read_excel(file)
        
        # التحقق من الأعمدة المطلوبة
        required_columns = ['اسم الخدمة', 'اسم الخدمة الفرعية']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            current_app.logger.error(f"أعمدة مفقودة: {missing_columns}")
            return jsonify({
                'success': False,
                'message': f'الأعمدة التالية مفقودة: {", ".join(missing_columns)}'
            }), 400
        
        # تجميع البيانات حسب الخدمة
        services_data = {}
        for index, row in df.iterrows():
            try:
                service_name = str(row['اسم الخدمة']).strip()
                sub_service_name = str(row['اسم الخدمة الفرعية']).strip()
                
                if not service_name or not sub_service_name:
                    current_app.logger.warning(f"تم تخطي الصف {index + 2} - بيانات فارغة")
                    continue
                
                if service_name not in services_data:
                    services_data[service_name] = set()
                
                services_data[service_name].add(sub_service_name)
            
            except Exception as e:
                current_app.logger.error(f"خطأ في معالجة الصف {index + 2}: {str(e)}")
                continue
        
        if not services_data:
            current_app.logger.error("لم يتم العثور على بيانات صالحة")
            return jsonify({
                'success': False,
                'message': 'لم يتم العثور على بيانات صالحة في الملف'
            }), 400
        
        # إضافة وتحديث البيانات
        current_app.logger.info("حفظ البيانات...")
        services_added = 0
        services_updated = 0
        sub_services_added = 0
        
        for service_name, sub_services in services_data.items():
            try:
                # البحث عن الخدمة
                existing_service = Service.query.filter_by(name=service_name).first()
                
                if existing_service:
                    # الخدمة موجودة - إضافة الخدمات الفرعية الجديدة فقط
                    current_sub_services = {sub.name for sub in existing_service.sub_services}
                    new_sub_services = sub_services - current_sub_services
                    
                    for sub_name in new_sub_services:
                        sub_service = SubService(
                            name=sub_name,
                            service=existing_service
                        )
                        db.session.add(sub_service)
                        sub_services_added += 1
                    
                    if new_sub_services:
                        services_updated += 1
                        current_app.logger.info(f"تم إضافة {len(new_sub_services)} خدمة فرعية جديدة للخدمة {service_name}")
                
                else:
                    # إنشاء خدمة جديدة مع خدماتها الفرعية
                    service = Service(name=service_name)
                    db.session.add(service)
                    
                    for sub_name in sub_services:
                        sub_service = SubService(
                            name=sub_name,
                            service=service
                        )
                        db.session.add(sub_service)
                        sub_services_added += 1
                    
                    services_added += 1
                    current_app.logger.info(f"تمت إضافة الخدمة {service_name} مع {len(sub_services)} خدمة فرعية")
            
            except Exception as e:
                current_app.logger.error(f"خطأ في معالجة الخدمة {service_name}: {str(e)}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'خطأ في معالجة الخدمة {service_name}'
                }), 500
        
        db.session.commit()
        message = []
        if services_added > 0:
            message.append(f'تم إضافة {services_added} خدمة جديدة')
        if services_updated > 0:
            message.append(f'تم تحديث {services_updated} خدمة موجودة')
        if sub_services_added > 0:
            message.append(f'تم إضافة {sub_services_added} خدمة فرعية')
        
        current_app.logger.info("تم الاستيراد بنجاح")
        return jsonify({
            'success': True,
            'message': ' و '.join(message)
        })
        
    except Exception as e:
        current_app.logger.error(f"خطأ في استيراد البيانات: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء استيراد البيانات'
        }), 500

@bp.route('/supervisors/template/download')
@login_required
@admin_required
def download_supervisor_template():
    """تنزيل نموذج Excel للمشرفين"""
    try:
        current_app.logger.info("بدء تنزيل نموذج المشرفين")
        
        # إنشاء ملف Excel مؤقت
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            workbook = xlsxwriter.Workbook(temp_file.name)
            worksheet = workbook.add_worksheet()
            
            # تنسيق العناوين
            header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#4F81BD',
                'font_color': 'white',
                'border': 1
            })
            
            # عناوين الأعمدة
            headers = [
                'رقم حساب المشرف',
                'اسم المشرف',
                'رقم حساب المندوب',
                'اسم المندوب'
            ]
            
            # كتابة العناوين
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
                worksheet.set_column(col, col, 20)  # تعيين عرض العمود
            
            # إضافة بيانات نموذجية
            sample_data = [
                ['12345', 'محمد أحمد', '67890', 'أحمد محمد'],
                ['12345', 'محمد أحمد', '67891', 'محمود علي'],  # نفس المشرف مع مندوب آخر
                ['12346', 'علي محمود', '67892', 'حسن محمد'],  # مشرف جديد
                ['12346', 'علي محمود', '67893', 'كريم أحمد']  # نفس المشرف الثاني مع مندوب آخر
            ]
            
            # تنسيق البيانات
            data_format = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            })
            
            # كتابة البيانات النموذجية
            for row, row_data in enumerate(sample_data, start=1):
                for col, cell_data in enumerate(row_data):
                    worksheet.write(row, col, cell_data, data_format)
            
            workbook.close()
            temp_file_path = temp_file.name
        
        current_app.logger.info("إرسال نموذج المشرفين")
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name='نموذج_المشرفين.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        current_app.logger.error(f"خطأ في تنزيل نموذج المشرفين: {str(e)}")
        flash('حدث خطأ أثناء تنزيل النموذج', 'error')
        return redirect(url_for('management.index'))

@bp.route('/service/template/download')
@login_required
@admin_required
def download_service_template():
    """تنزيل نموذج Excel للخدمات"""
    try:
        template_path = os.path.join(current_app.config['BASE_DIR'], 'services_template.xlsx')
        return send_file(
            template_path,
            as_attachment=True,
            download_name='نموذج_الخدمات.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        current_app.logger.error(f"خطأ في تنزيل نموذج الخدمات: {str(e)}")
        flash('حدث خطأ أثناء تنزيل النموذج', 'error')
        return redirect(url_for('management.index'))

@bp.route('/supervisors/export')
@login_required
@admin_required
def export_supervisors():
    """تصدير المشرفين إلى ملف Excel"""
    try:
        current_app.logger.info("بدء عملية تصدير المشرفين")
        
        # جلب جميع المشرفين مع المناديب
        supervisors = Supervisor.query.all()
        current_app.logger.info(f"تم العثور على {len(supervisors)} مشرف")
        
        # تحضير البيانات للتصدير
        data = []
        for supervisor in supervisors:
            current_app.logger.info(f"معالجة المشرف: {supervisor.name}")
            for representative in supervisor.representatives:
                data.append([
                    supervisor.account_number,
                    supervisor.name,
                    representative.account_number,
                    representative.name
                ])
        
        # عناوين الأعمدة
        headers = [
            'رقم حساب المشرف',
            'اسم المشرف',
            'رقم حساب المندوب',
            'اسم المندوب'
        ]
        
        current_app.logger.info("إنشاء ملف Excel")
        # إنشاء ملف Excel مؤقت
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            workbook = xlsxwriter.Workbook(temp_file.name)
            worksheet = workbook.add_worksheet()
            
            # تنسيق العناوين
            header_format = workbook.add_format({
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#4F81BD',
                'font_color': 'white',
                'border': 1
            })
            
            # تنسيق البيانات
            data_format = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            })
            
            # كتابة العناوين
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
                worksheet.set_column(col, col, 20)  # تعيين عرض العمود
            
            # كتابة البيانات
            for row, row_data in enumerate(data, start=1):
                for col, cell_data in enumerate(row_data):
                    worksheet.write(row, col, cell_data, data_format)
            
            workbook.close()
            temp_file_path = temp_file.name
        
        current_app.logger.info("إرسال الملف")
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name='المشرفين_والمناديب.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        current_app.logger.error(f"خطأ في تصدير المشرفين: {str(e)}")
        flash('حدث خطأ أثناء تصدير البيانات', 'error')
        return redirect(url_for('management.index'))