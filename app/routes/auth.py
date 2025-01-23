from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models.user import User
from app.forms.auth import LoginForm, RegisterForm
from app import db
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        current_app.logger.info(f'محاولة تسجيل دخول برقم الحساب: {form.account_number.data}')
        user = User.query.filter_by(account_number=form.account_number.data).first()
        if user:
            current_app.logger.info(f'تم العثور على المستخدم: {user.username}')
            if check_password_hash(user.password, form.password.data):
                current_app.logger.info('كلمة المرور صحيحة')
                login_user(user, remember=form.remember_me.data)
                current_app.logger.info(f'تم تسجيل الدخول بنجاح. تذكرني: {form.remember_me.data}')
                next_page = request.args.get('next')
                flash(f'مرحباً {user.username}! تم تسجيل دخولك بنجاح', 'success')
                return redirect(next_page or url_for('dashboard.index'))
            else:
                current_app.logger.warning('كلمة المرور غير صحيحة')
        else:
            current_app.logger.warning('لم يتم العثور على المستخدم')
        flash('رقم الحساب أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('auth/login.html', form=form, now=datetime.now())

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            current_app.logger.info('=== بدء عملية تسجيل مستخدم جديد ===')
            current_app.logger.info(f'البيانات المرسلة:')
            current_app.logger.info(f'رقم الحساب: {form.account_number.data}')
            current_app.logger.info(f'اسم المستخدم: {form.username.data}')
            current_app.logger.info(f'البريد الإلكتروني: {form.email.data}')
            
            # التحقق من عدم وجود المستخدم
            if User.query.filter_by(account_number=form.account_number.data).first():
                current_app.logger.warning(f'رقم الحساب {form.account_number.data} مستخدم بالفعل')
                flash('رقم الحساب مستخدم بالفعل', 'error')
                return render_template('auth/register.html', form=form, now=datetime.now())
            
            if User.query.filter_by(email=form.email.data).first():
                current_app.logger.warning(f'البريد الإلكتروني {form.email.data} مستخدم بالفعل')
                flash('البريد الإلكتروني مستخدم بالفعل', 'error')
                return render_template('auth/register.html', form=form, now=datetime.now())
            
            # إنشاء المستخدم
            user = User(
                account_number=form.account_number.data,
                username=form.username.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
                role='sales'  # تعيين الدور كمبيعات افتراضياً
            )
            db.session.add(user)
            db.session.commit()
            
            current_app.logger.info(f'تم إنشاء المستخدم بنجاح. معرف المستخدم: {user.id}')
            flash('تم إنشاء حسابك بنجاح! يمكنك الآن تسجيل الدخول', 'success')
            flash(f'رقم حسابك هو: {user.account_number}، احتفظ به للدخول إلى النظام', 'info')
            flash('سيتم تحويلك إلى صفحة تسجيل الدخول...', 'info')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            current_app.logger.error(f'خطأ في إنشاء المستخدم: {str(e)}')
            db.session.rollback()
            flash('حدث خطأ أثناء إنشاء الحساب. يرجى المحاولة مرة أخرى', 'error')
    else:
        if form.errors:
            current_app.logger.warning('أخطاء في النموذج:')
            for field, errors in form.errors.items():
                current_app.logger.warning(f'{field}: {", ".join(errors)}')
    
    return render_template('auth/register.html', form=form, now=datetime.now())

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('auth.login')) 