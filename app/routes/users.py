from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User
from app.forms.user import UserForm, EditUserForm, ChangePasswordForm
from app.utils.decorators import admin_required
from app import db

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/')
@login_required
@admin_required
def index():
    """عرض قائمة المستخدمين"""
    users = User.query.filter(User.role.in_(['support', 'sales'])).all()
    return render_template('users/index.html', users=users)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """إنشاء مستخدم جديد"""
    form = UserForm()
    if form.validate_on_submit():
        try:
            current_app.logger.info('=== بدء عملية إنشاء مستخدم جديد ===')
            current_app.logger.info(f'البيانات المرسلة:')
            current_app.logger.info(f'اسم المستخدم: {form.username.data}')
            current_app.logger.info(f'البريد الإلكتروني: {form.email.data}')
            current_app.logger.info(f'رقم الحساب: {form.account_number.data}')
            current_app.logger.info(f'الصلاحية: {form.role.data}')
            
            user = User(
                account_number=form.account_number.data,
                username=form.username.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
                role=form.role.data,
                supervisor_account=form.supervisor_account.data,
                supervisor_name=form.supervisor_name.data
            )
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f'تم إنشاء المستخدم بنجاح. معرف المستخدم: {user.id}')
            flash('تم إنشاء المستخدم بنجاح', 'success')
            return redirect(url_for('users.index'))
        except Exception as e:
            current_app.logger.error(f'خطأ في إنشاء المستخدم: {str(e)}')
            db.session.rollback()
            flash('حدث خطأ أثناء إنشاء المستخدم', 'error')
    else:
        if form.errors:
            current_app.logger.warning('أخطاء في النموذج:')
            for field, errors in form.errors.items():
                current_app.logger.warning(f'{field}: {", ".join(errors)}')
    
    return render_template('users/create.html', form=form)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    """تعديل بيانات المستخدم"""
    user = User.query.get_or_404(id)
    if user.role == 'admin':
        flash('لا يمكن تعديل بيانات المدير', 'error')
        return redirect(url_for('users.index'))
    
    form = EditUserForm()
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.account_number = form.account_number.data
        user.supervisor_account = form.supervisor_account.data
        user.supervisor_name = form.supervisor_name.data
        user.role = form.role.data
        db.session.commit()
        flash('تم تحديث بيانات المستخدم بنجاح', 'success')
        return redirect(url_for('users.index'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.account_number.data = user.account_number
        form.supervisor_account.data = user.supervisor_account
        form.supervisor_name.data = user.supervisor_name
        form.role.data = user.role
    
    return render_template('users/edit.html', form=form, user=user)

@bp.route('/<int:id>/change-password', methods=['GET', 'POST'])
@login_required
@admin_required
def change_password(id):
    """تغيير كلمة مرور المستخدم"""
    user = User.query.get_or_404(id)
    if user.role == 'admin':
        flash('لا يمكن تغيير كلمة مرور المدير', 'error')
        return redirect(url_for('users.index'))
    
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('تم تغيير كلمة المرور بنجاح', 'success')
        return redirect(url_for('users.index'))
    return render_template('users/change_password.html', form=form, user=user)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(id):
    """حذف مستخدم"""
    user = User.query.get_or_404(id)
    if user.role == 'admin':
        return jsonify({'error': 'لا يمكن حذف المدير'}), 403
    
    # التحقق من وجود شكاوى مرتبطة
    if user.complaints:
        return jsonify({'error': 'لا يمكن حذف المستخدم - يوجد شكاوى مرتبطة به'}), 400
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف المستخدم بنجاح'})
    except Exception as e:
        current_app.logger.error(f'خطأ في حذف المستخدم: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'حدث خطأ أثناء حذف المستخدم'}), 500 