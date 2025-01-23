from PIL import Image, ImageDraw

# إنشاء صورة جديدة بحجم 32x32 بكسل
img = Image.new('RGB', (32, 32), color='white')
draw = ImageDraw.Draw(img)

# رسم دائرة زرقاء
draw.ellipse([4, 4, 28, 28], fill='#0d6efd')

# رسم حرف C باللون الأبيض
draw.text((10, 8), 'C', fill='white', font=None)

# حفظ الصورة كـ favicon
img.save('app/static/images/favicon.ico') 