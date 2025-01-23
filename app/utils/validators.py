from werkzeug.utils import secure_filename
import os
from flask import current_app

ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif'},
    'document': {'pdf', 'doc', 'docx', 'xls', 'xlsx'},
    'all': {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
}

def validate_file_extension(filename, file_type='all'):
    """
    التحقق من امتداد الملف
    
    :param filename: اسم الملف
    :param file_type: نوع الملف (image, document, all)
    :return: True إذا كان الامتداد مسموحاً به
    """
    try:
        current_app.logger.debug(f'التحقق من امتداد الملف: {filename}')
        if '.' not in filename:
            current_app.logger.error(f'لا يوجد امتداد في اسم الملف: {filename}')
            return False
            
        extension = filename.rsplit('.', 1)[1].lower()
        current_app.logger.debug(f'امتداد الملف: {extension}')
        current_app.logger.debug(f'الامتدادات المسموح بها: {ALLOWED_EXTENSIONS.get(file_type, ALLOWED_EXTENSIONS["all"])}')
        
        is_valid = extension in ALLOWED_EXTENSIONS.get(file_type, ALLOWED_EXTENSIONS['all'])
        current_app.logger.debug(f'نتيجة التحقق من الامتداد: {is_valid}')
        return is_valid
    except Exception as e:
        current_app.logger.error(f'خطأ في التحقق من امتداد الملف: {str(e)}')
        return False

def validate_file_size(file, max_size_mb=5):
    """
    التحقق من حجم الملف
    
    :param file: كائن الملف
    :param max_size_mb: الحجم الأقصى بالميجابايت
    :return: True إذا كان الحجم مسموحاً به
    """
    try:
        current_app.logger.debug(f'التحقق من حجم الملف: {file.filename}')
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        max_size = max_size_mb * 1024 * 1024
        current_app.logger.debug(f'حجم الملف: {size} بايت')
        current_app.logger.debug(f'الحجم الأقصى المسموح به: {max_size} بايت')
        
        is_valid = size <= max_size
        current_app.logger.debug(f'نتيجة التحقق من الحجم: {is_valid}')
        return is_valid
    except Exception as e:
        current_app.logger.error(f'خطأ في التحقق من حجم الملف: {str(e)}')
        return False