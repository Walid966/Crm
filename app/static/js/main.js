// تهيئة التنبيهات
document.addEventListener('DOMContentLoaded', function() {
    // تحويل رسائل الفلاش إلى إشعارات
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const message = alert.textContent.trim();
        const type = alert.classList.contains('alert-success') ? 'success' :
                    alert.classList.contains('alert-danger') ? 'error' :
                    alert.classList.contains('alert-warning') ? 'warning' : 'info';
        
        showNotification(message, type);
        alert.remove();
    });
});

// تحديث الإشعارات
function updateNotifications() {
    const badge = document.querySelector('.notification-badge');
    const container = document.querySelector('.notifications-container');
    
    if (badge && container) {
        fetch('/api/notifications/unread')
            .then(response => response.json())
            .then(data => {
                if (data.length > 0) {
                    badge.textContent = data.length;
                    badge.style.display = 'block';
                    
                    container.innerHTML = data.map(notification => `
                        <a href="${notification.link}" class="dropdown-item">
                            <small class="text-muted">${new Date(notification.created_at).toLocaleString()}</small>
                            <p class="mb-0">${notification.message}</p>
                        </a>
                    `).join('');
                    
                    // تشغيل صوت الإشعار للإشعارات الجديدة
                    showNotification('لديك إشعارات جديدة', 'info');
                } else {
                    badge.style.display = 'none';
                    container.innerHTML = '<div class="dropdown-item text-center">لا توجد إشعارات جديدة</div>';
                }
            })
            .catch(error => {
                console.error('خطأ في تحديث الإشعارات:', error);
                showNotification('حدث خطأ في تحديث الإشعارات', 'error');
            });
    }
}

// تحديث الإشعارات كل دقيقة
if (document.querySelector('.notification-badge')) {
    updateNotifications();
    setInterval(updateNotifications, 60000);
}

// معاينة الصور قبل الرفع
function previewImage(input, imgElement) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            imgElement.src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// تأكيد الحذف
function confirmDelete(message, callback) {
    if (confirm(message || 'هل أنت متأكد من الحذف؟')) {
        callback();
    }
}

// إظهار شاشة التحميل
function showLoading() {
    const loading = document.createElement('div');
    loading.className = 'loading';
    loading.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(loading);
}

// إخفاء شاشة التحميل
function hideLoading() {
    const loading = document.querySelector('.loading');
    if (loading) {
        loading.remove();
    }
}

// معالجة الأخطاء
function handleError(error, message = 'حدث خطأ') {
    console.error(error);
    showNotification(message, 'error');
}

// معالجة النجاح
function handleSuccess(message) {
    showNotification(message, 'success');
}

// تنسيق التواريخ
function formatDate(date) {
    return new Date(date).toLocaleDateString('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// تحويل النص العادي إلى HTML
function nl2br(str) {
    return str.replace(/\n/g, '<br>');
}

// إرسال النماذج بـ AJAX
function submitForm(form, callback) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitButton = form.querySelector('[type="submit"]');
        const originalText = submitButton.innerHTML;
        
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الإرسال...';
        
        fetch(form.action, {
            method: form.method,
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            
            if (callback) {
                callback(data);
            }
        })
        .catch(error => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            alert('حدث خطأ أثناء الإرسال');
        });
    });
}

// تحديث حالة الشكوى
function updateComplaintStatus(complaintId, status) {
    showLoading();
    
    fetch(`/api/complaints/${complaintId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        location.reload();
    })
    .catch(error => {
        hideLoading();
        alert('حدث خطأ أثناء تحديث الحالة');
    });
}

// تحميل المزيد من النتائج
function loadMore(button, url, container) {
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري التحميل...';
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            container.insertAdjacentHTML('beforeend', data.html);
            
            if (data.has_more) {
                button.dataset.page = data.next_page;
                button.disabled = false;
                button.innerHTML = 'تحميل المزيد';
            } else {
                button.remove();
            }
        })
        .catch(error => {
            button.disabled = false;
            button.innerHTML = 'تحميل المزيد';
            alert('حدث خطأ أثناء التحميل');
        });
} 