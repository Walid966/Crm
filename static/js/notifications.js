// إعداد Socket.IO
const socket = io();

// عند الاتصال بالخادم
socket.on('connect', function() {
    console.log('تم الاتصال بالخادم');
    // طلب الإشعارات غير المقروءة عند الاتصال
    socket.emit('request_notifications');
});

// عند استلام إشعار جديد
socket.on('notification', function(data) {
    console.log('تم استلام إشعار:', data);
    showNotification(data.message);
    updateNotificationCount();
});

function showNotification(message) {
    // إنشاء عنصر الإشعار
    const notification = document.createElement('div');
    notification.className = 'toast';
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    notification.setAttribute('aria-atomic', 'true');
    notification.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">إشعار جديد</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    // إضافة الإشعار إلى الصفحة
    let container = document.getElementById('notifications-container');
    if (!container) {
        // إنشاء حاوية لإشعارات إذا لم تكن موجودة
        container = document.createElement('div');
        container.id = 'notifications-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.left = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    container.appendChild(notification);

    // تفعيل الإشعار
    const toast = new bootstrap.Toast(notification, {
        autohide: true,
        delay: 5000
    });
    toast.show();

    // تشغيل صوت التنبيه
    playNotificationSound();
}

function updateNotificationCount() {
    fetch('/unread_notifications_count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notifications-badge');
            if (badge) {
                badge.textContent = data.count;
                badge.style.display = data.count > 0 ? 'inline' : 'none';
            }
        })
        .catch(error => console.error('خطأ في تحديث عدد الإشعارات:', error));
}

function playNotificationSound() {
    // إنشاء عنصر الصوت
    const audio = new Audio('/static/sounds/notification.mp3');
    audio.play().catch(error => {
        // تجاهل أخطاء تشغيل الصوت (قد يحدث في بعض المتصفحات)
        console.log('لم يتم تشغيل صوت الإشعار:', error);
    });
}

// تحديث عدد الإشعارات عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    updateNotificationCount();
}); 