from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """مصادقة المدير وموظف الدعم"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'support']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def support_required(f):
    """مصادقة موظف الدعم"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'support']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def sales_required(f):
    """مصادقة مستخدم المبيعات"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'sales':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function 