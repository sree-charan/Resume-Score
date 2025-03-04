// Resume Analysis System - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Handle file input styling and validation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.files.length > 0) {
                const label = this.nextElementSibling;
                if (label && label.classList.contains('form-file-label')) {
                    label.textContent = `${this.files.length} file(s) selected`;
                }
            }
        });
    });
    
    // Add active class to current nav item
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });
    
    // Enable sorting for tables with the sortable class
    const sortableTables = document.querySelectorAll('table.sortable');
    sortableTables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            if (!header.classList.contains('no-sort')) {
                header.addEventListener('click', function() {
                    sortTable(table, index);
                });
                header.style.cursor = 'pointer';
                header.title = 'Click to sort';
                
                // Add sort icon
                const icon = document.createElement('i');
                icon.classList.add('fas', 'fa-sort', 'ms-2', 'text-muted');
                header.appendChild(icon);
            }
        });
    });
});

// Table sorting function
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const headers = table.querySelectorAll('th');
    const header = headers[columnIndex];
    
    // Determine sort direction
    const isAscending = header.classList.contains('sort-asc') ? false : true;
    
    // Reset all headers
    headers.forEach(h => {
        h.classList.remove('sort-asc', 'sort-desc');
        const icon = h.querySelector('i.fas');
        if (icon) {
            icon.className = 'fas fa-sort ms-2 text-muted';
        }
    });
    
    // Set sort direction on the clicked header
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
    const icon = header.querySelector('i.fas');
    if (icon) {
        icon.className = `fas fa-sort-${isAscending ? 'up' : 'down'} ms-2 text-primary`;
    }
    
    // Sort the rows
    rows.sort((rowA, rowB) => {
        const cellA = rowA.querySelectorAll('td')[columnIndex].textContent.trim();
        const cellB = rowB.querySelectorAll('td')[columnIndex].textContent.trim();
        
        if (!isNaN(parseFloat(cellA)) && !isNaN(parseFloat(cellB))) {
            // Numeric sort
            return isAscending ? 
                parseFloat(cellA) - parseFloat(cellB) : 
                parseFloat(cellB) - parseFloat(cellA);
        } else {
            // Text sort
            return isAscending ? 
                cellA.localeCompare(cellB) : 
                cellB.localeCompare(cellA);
        }
    });
    
    // Clear and re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

// File type validation
function validateFileType(input, allowedTypes) {
    const files = input.files;
    let isValid = true;
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileExt = file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExt)) {
            isValid = false;
            break;
        }
    }
    
    if (!isValid) {
        alert('Invalid file type! Please select only supported file types: ' + allowedTypes.join(', '));
        input.value = '';
    }
    
    return isValid;
}

// Function to copy text to clipboard
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    
    // Show a toast notification
    const toast = document.createElement('div');
    toast.className = 'position-fixed bottom-0 end-0 p-3';
    toast.style.zIndex = 11;
    
    toast.innerHTML = `
        <div class="toast align-items-center text-white bg-success" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-check-circle me-2"></i> Text copied to clipboard!
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    document.body.appendChild(toast);
    const toastEl = new bootstrap.Toast(toast.querySelector('.toast'));
    toastEl.show();
    
    setTimeout(() => {
        document.body.removeChild(toast);
    }, 3000);
}