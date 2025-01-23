import io
import xlsxwriter
from flask import current_app

def generate_excel(headers, data):
    """إنشاء ملف Excel"""
    current_app.logger.info(f'generate_excel called with headers: {headers}')
    current_app.logger.info(f'generate_excel called with {len(data)} rows of data')
    
    output = io.BytesIO()
    
    try:
        # إنشاء ملف Excel جديد
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('الشكاوى')
        
        # تنسيق العناوين
        header_format = workbook.add_format({
            'bold': True,
            'font_name': 'Arial',
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4CAF50',
            'font_color': 'white',
            'border': 1,
            'text_wrap': True,
        })
        
        # تنسيق البيانات
        data_format = workbook.add_format({
            'font_name': 'Arial',
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'border': 1,
        })
        
        # تعيين اتجاه الكتابة من اليمين إلى اليسار
        worksheet.right_to_left()
        
        # تعيين عرض الأعمدة
        column_widths = {
            0: 10,  # رقم الشكوى
            1: 25,  # المشرف
            2: 25,  # المندوب
            3: 15,  # التاجر
            4: 15,  # رقم العملية
            5: 20,  # الخدمة
            6: 20,  # الخدمة الفرعية
            7: 15,  # الحالة
            8: 20,  # تاريخ الإنشاء
            9: 30,  # الملاحظات
        }
        
        # كتابة العناوين
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, column_widths.get(col, 15))
            current_app.logger.debug(f'Writing header: {header} at column {col}')
        
        # كتابة البيانات
        for row_idx, row_data in enumerate(data, start=1):
            current_app.logger.debug(f'Writing row {row_idx}: {row_data}')
            for col_idx, cell_data in enumerate(row_data):
                try:
                    worksheet.write(row_idx, col_idx, cell_data, data_format)
                    current_app.logger.debug(f'Wrote cell ({row_idx}, {col_idx}): {cell_data}')
                except Exception as cell_error:
                    current_app.logger.error(f'Error writing cell ({row_idx}, {col_idx}): {str(cell_error)}')
                    worksheet.write(row_idx, col_idx, str(cell_data), data_format)
        
        # تجميد الصف الأول
        worksheet.freeze_panes(1, 0)
        
        # إضافة فلتر للأعمدة
        worksheet.autofilter(0, 0, len(data), len(headers) - 1)
        
        # إغلاق الملف
        workbook.close()
        
        # إعادة تعيين مؤشر البيانات إلى البداية
        output.seek(0)
        
        current_app.logger.info('Excel file generated successfully')
        return output
        
    except Exception as e:
        current_app.logger.error(f'Error generating Excel file: {str(e)}')
        raise