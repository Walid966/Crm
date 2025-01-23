import io
import xlsxwriter

def generate_excel(data, headers):
    """
    توليد ملف Excel من البيانات
    
    :param data: قائمة من الصفوف
    :param headers: قائمة من عناوين الأعمدة
    :return: كائن BytesIO يحتوي على ملف Excel
    """
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
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
    
    # كتابة البيانات
    for row, row_data in enumerate(data, start=1):
        for col, cell_data in enumerate(row_data):
            worksheet.write(row, col, cell_data, data_format)
    
    # تعديل عرض الأعمدة
    for i in range(len(headers)):
        worksheet.set_column(i, i, 15)
    
    workbook.close()
    output.seek(0)
    return output 