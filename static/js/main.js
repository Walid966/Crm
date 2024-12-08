// تحديث الخدمات الفرعية عند تغيير نوع الخدمة
document.addEventListener('DOMContentLoaded', function() {
    const serviceSelect = document.getElementById('service_type');
    const subServiceSelect = document.getElementById('sub_service');
    
    if (serviceSelect && subServiceSelect) {
        serviceSelect.addEventListener('change', function() {
            const serviceId = this.value;
            fetch(`/get_sub_services/${serviceId}`)
                .then(response => response.json())
                .then(data => {
                    subServiceSelect.innerHTML = '';
                    data.forEach(subService => {
                        const option = document.createElement('option');
                        option.value = subService.id;
                        option.textContent = subService.name;
                        subServiceSelect.appendChild(option);
                    });
                });
        });
    }
});

// تحديث المناديب عند تغيير المشرف
const supervisorSelect = document.getElementById('supervisor_account');
const representativeSelect = document.getElementById('representative_account');

if (supervisorSelect && representativeSelect) {
    supervisorSelect.addEventListener('change', function() {
        const supervisorId = this.value;
        fetch(`/get_representatives/${supervisorId}`)
            .then(response => response.json())
            .then(data => {
                representativeSelect.innerHTML = '';
                data.forEach(representative => {
                    const option = document.createElement('option');
                    option.value = representative.id;
                    option.textContent = representative.name;
                    representativeSelect.appendChild(option);
                });
            });
    });
}

// تفعيل البحث المباشر في الجداول
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchText = this.value.toLowerCase();
            const table = document.querySelector('table');
            const rows = table.getElementsByTagName('tr');

            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const cells = row.getElementsByTagName('td');
                let found = false;

                for (let j = 0; j < cells.length; j++) {
                    const cell = cells[j];
                    if (cell.textContent.toLowerCase().indexOf(searchText) > -1) {
                        found = true;
                        break;
                    }
                }

                row.style.display = found ? '' : 'none';
            }
        });
    }
}); 

// تحسين البحث في الجداول
function filterTable(tableId, searchText) {
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');
    const searchTerms = searchText.toLowerCase().split(' ');

    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        let found = true;

        for (const term of searchTerms) {
            let termFound = false;
            for (let j = 0; j < cells.length; j++) {
                if (cells[j].textContent.toLowerCase().includes(term)) {
                    termFound = true;
                    break;
                }
            }
            if (!termFound) {
                found = false;
                break;
            }
        }

        row.style.display = found ? '' : 'none';
    }
}

// تحسين الفلترة حسب الحالة
function filterByStatus(status) {
    const rows = document.querySelectorAll('table tbody tr');
    rows.forEach(row => {
        const statusCell = row.querySelector('td:nth-child(6)');
        if (status === '' || statusCell.textContent.trim() === status) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
} 

// تصفية الشكاوى حسب التاريخ والحالة
function filterComplaints() {
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const status = document.getElementById('statusFilter').value;
    const rows = document.querySelectorAll('table tbody tr');

    rows.forEach(row => {
        const dateCell = row.querySelector('td:nth-child(7)').textContent;
        const statusCell = row.querySelector('td:nth-child(6)').textContent.trim();
        const date = new Date(dateCell);
        
        let showRow = true;
        if (dateFrom && date < new Date(dateFrom)) showRow = false;
        if (dateTo && date > new Date(dateTo)) showRow = false;
        if (status && statusCell !== status) showRow = false;

        row.style.display = showRow ? '' : 'none';
    });
}

// إضافة عناصر التصفية في HTML
const filterSection = document.querySelector('.filter-section');
if (filterSection) {
    filterSection.innerHTML += `
        <input type="date" id="dateFrom" class="form-control mx-1" onchange="filterComplaints()">
        <input type="date" id="dateTo" class="form-control mx-1" onchange="filterComplaints()">
    `;
} 

// تأكيد الحذف
function confirmDelete(formId) {
    if (confirm('هل أنت متأكد من الحذف؟')) {
        document.getElementById(formId).submit();
    }
    return false;
} 

// تهيئة النوافذ المنبثقة
document.addEventListener('DOMContentLoaded', function() {
    // تهيئة جميع النوافذ المنبثقة
    var modals = [].slice.call(document.querySelectorAll('.modal'));
    modals.forEach(function(modal) {
        new bootstrap.Modal(modal);
    });

    // تهيئة tooltips
    var tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.forEach(function(tooltip) {
        new bootstrap.Tooltip(tooltip);
    });

    // تهيئة popovers
    var popovers = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popovers.forEach(function(popover) {
        new bootstrap.Popover(popover);
    });
}); 