import os
from werkzeug.utils import secure_filename
from flask import current_app
import uuid

def save_file(file, subfolder=''):
    """حفظ الملف في المجلد المحدد"""
    try:
        if not file:
            return None
            
        # إنشاء اسم فريد للملف
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{str(uuid.uuid4())[:8]}{ext}"
        
        # إنشاء المجلد إذا لم يكن موجوداً
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # حفظ الملف
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # إرجاع المسار النسبي للملف باستخدام / بدلاً من \
        return os.path.join(subfolder, unique_filename).replace('\\', '/')
        
    except Exception as e:
        current_app.logger.error(f'خطأ في حفظ الملف: {str(e)}')
        raise

def delete_file(filepath):
    """حذف الملف من المجلد المحدد"""
    try:
        if not filepath:
            return
            
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filepath)
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        current_app.logger.error(f'خطأ في حذف الملف: {str(e)}')
        raise 