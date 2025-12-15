// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Mobile Navigation Toggle
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    // Close flash messages
    document.querySelectorAll('.alert-close').forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });

    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        });
    }, 5000);

    // Form validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const password = this.querySelector('[name="password"]');
            const confirmPassword = this.querySelector('[name="confirm_password"]');
            
            if (password && confirmPassword && password.value !== confirmPassword.value) {
                e.preventDefault();
                alert('Passwords do not match!');
                return false;
            }
        });
    });

    // Dropdown menu handling
    document.querySelectorAll('.dropdown').forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (toggle && menu) {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Close all other dropdowns
                document.querySelectorAll('.dropdown-menu').forEach(otherMenu => {
                    if (otherMenu !== menu) {
                        otherMenu.style.display = 'none';
                    }
                });
                
                // Toggle current dropdown
                menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
            });
        }
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', () => {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.style.display = 'none';
        });
    });
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Loading state for buttons
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }
    });
});

// Confirm delete actions
document.querySelectorAll('[data-confirm]').forEach(element => {
    element.addEventListener('click', function(e) {
        if (!confirm(this.getAttribute('data-confirm'))) {
            e.preventDefault();
            return false;
        }
    });
});

// Character counter for textareas
document.querySelectorAll('textarea[maxlength]').forEach(textarea => {
    const maxLength = textarea.getAttribute('maxlength');
    const counter = document.createElement('div');
    counter.style.cssText = 'text-align: right; font-size: 0.875rem; color: var(--gray-500); margin-top: 0.25rem;';
    counter.textContent = `0 / ${maxLength}`;
    textarea.parentNode.appendChild(counter);
    
    textarea.addEventListener('input', function() {
        counter.textContent = `${this.value.length} / ${maxLength}`;
    });
});

// Image preview for file uploads
document.querySelectorAll('input[type="file"][accept*="image"]').forEach(input => {
    input.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                let preview = input.parentNode.querySelector('.image-preview');
                if (!preview) {
                    preview = document.createElement('img');
                    preview.className = 'image-preview';
                    preview.style.cssText = 'max-width: 200px; margin-top: 1rem; border-radius: var(--border-radius);';
                    input.parentNode.appendChild(preview);
                }
                preview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });
});

// Real-time search
const searchInputs = document.querySelectorAll('[data-search]');
searchInputs.forEach(input => {
    let timeout;
    input.addEventListener('input', function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            const query = this.value.toLowerCase();
            const target = document.querySelector(this.getAttribute('data-search'));
            if (target) {
                target.querySelectorAll('[data-searchable]').forEach(item => {
                    const text = item.textContent.toLowerCase();
                    item.style.display = text.includes(query) ? '' : 'none';
                });
            }
        }, 300);
    });
});

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        ${message}
        <button class="alert-close">&times;</button>
    `;
    
    const container = document.querySelector('.flash-messages') || createFlashContainer();
    container.appendChild(toast);
    
    toast.querySelector('.alert-close').addEventListener('click', () => {
        toast.remove();
    });
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

// Export for use in other scripts
window.showToast = showToast;

// Socket.IO event handler for interest decisions (Professional UI)
// This listens for accept/reject decisions from institutions
if (typeof io !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        // Check if socket is already initialized elsewhere
        if (window.socket) {
            // Listen for interest_decision event
            window.socket.on('interest_decision', function(data) {
                console.log('Received interest decision:', data);
                
                const decision = data.decision;
                const gigTitle = data.gig_title;
                const institutionName = data.institution_name;
                
                // Show toast notification
                const message = decision === 'accepted' 
                    ? `🎉 Great news! Your interest in "${gigTitle}" was accepted by ${institutionName}!`
                    : `Your interest in "${gigTitle}" was rejected by ${institutionName}.`;
                
                showToast(message, decision === 'accepted' ? 'success' : 'error');
                
                // Update notification badge if function exists
                if (window.updateNotificationBadge) {
                    window.updateNotificationBadge();
                }
                
                // Disable express interest button if on gig detail page
                const interestBtn = document.querySelector(`[data-gig-id="${data.gig_id}"]`);
                if (interestBtn) {
                    interestBtn.disabled = true;
                    interestBtn.textContent = decision === 'accepted' ? 'Accepted' : 'Rejected';
                    interestBtn.style.backgroundColor = decision === 'accepted' ? '#10b981' : '#ef4444';
                }
            });
        }
    });
}
