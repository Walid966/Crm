// إعداد صوت الإشعارات
const notificationSound = new Audio('/static/sounds/notification.mp3');

function playNotificationSound() {
    notificationSound.play().catch(error => {
        console.log('فشل تشغيل صوت الإشعار:', error);
    });
}

function showNotification(message, type = 'info') {
    // تشغيل الصوت
    playNotificationSound();
    
    // إظهار الإشعار
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-top-left",
        timeOut: 5000,
        rtl: true
    };
    
    switch(type) {
        case 'success':
            toastr.success(message);
            break;
        case 'error':
            toastr.error(message);
            break;
        case 'warning':
            toastr.warning(message);
            break;
        default:
            toastr.info(message);
    }
}

// استمع لأحداث الإشعارات من الخادم
const socket = io();

socket.on('notification', function(data) {
    showNotification(data.message, data.type);
});

// دالة لإرسال إشعار
function sendNotification(message, type = 'info') {
    socket.emit('send_notification', {
        message: message,
        type: type
    });
}