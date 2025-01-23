import io
from weasyprint import HTML

def generate_pdf(html_content):
    """
    توليد ملف PDF من محتوى HTML
    
    :param html_content: محتوى HTML كنص
    :return: كائن BytesIO يحتوي على ملف PDF
    """
    output = io.BytesIO()
    HTML(string=html_content).write_pdf(output)
    output.seek(0)
    return output 