// إعداد صوت الإشعارات
const notificationSound = new Audio('/static/sounds/notification.mp3');

function playNotificationSound() {
    notificationSound.play().catch(error => {
        console.log('فشل تشغيل صوت الإشعار:', error);
    });
}

// الإعدادات الافتراضية لـ toastr
toastr.options = {
    closeButton: true,
    progressBar: true,
    positionClass: "toast-top-left",
    timeOut: 5000,
    rtl: true,
    onShown: function() {
        playNotificationSound();
    }
};

// تعديل دوال toastr الأصلية لتشغيل الصوت
const originalSuccess = toastr.success;
const originalError = toastr.error;
const originalWarning = toastr.warning;
const originalInfo = toastr.info;

toastr.success = function(message, title, options) {
    playNotificationSound();
    return originalSuccess.call(this, message, title, options);
};

toastr.error = function(message, title, options) {
    playNotificationSound();
    return originalError.call(this, message, title, options);
};

toastr.warning = function(message, title, options) {
    playNotificationSound();
    return originalWarning.call(this, message, title, options);
};

toastr.info = function(message, title, options) {
    playNotificationSound();
    return originalInfo.call(this, message, title, options);
}; 