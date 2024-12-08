import wave
import struct
import math
import os

def create_beep(filename, duration=0.3, frequency=440.0, volume=0.5):
    # معدل العينات
    sample_rate = 44100
    
    # عدد العينات
    n_samples = int(duration * sample_rate)
    
    # إنشاء البيانات
    data = []
    for i in range(n_samples):
        t = float(i) / sample_rate
        # موجة جيبية بسيطة
        value = volume * math.sin(2.0 * math.pi * frequency * t)
        # تحويل إلى 16-bit integer
        packed_value = struct.pack('h', int(value * 32767.0))
        data.append(packed_value)
    
    # إنشاء مجلد الأصوات إذا لم يكن موجوداً
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # كتابة الملف
    with wave.open(filename, 'wb') as wav_file:
        # تعيين معلمات الملف
        n_channels = 1
        sample_width = 2
        wav_file.setnchannels(n_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        # كتابة البيانات
        wav_file.writeframes(b''.join(data))

if __name__ == '__main__':
    create_beep('static/sounds/notification.mp3') 