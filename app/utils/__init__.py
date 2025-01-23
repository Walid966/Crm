from .excel import generate_excel
from .notifications import send_notification
from .validators import validate_file_extension, validate_file_size
from .decorators import admin_required, support_required
from .files import save_file, delete_file
from .email import send_email

def generate_pdf(html_content):
    """
    نسخة احتياطية من دالة توليد PDF في حالة عدم توفر WeasyPrint
    """
    return None 