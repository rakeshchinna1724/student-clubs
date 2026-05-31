// Student Club - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializePageLoader();
    // Initialize animations
    initializeAnimations();
    initializeFormValidation();
    initializeInteractiveElements();
    updateNotificationCount();
});

/**
 * Show a short loading overlay during page navigation.
 */
function initializePageLoader() {
    const loader = document.getElementById('pageLoader');
    if (!loader) {
        return;
    }

    const showLoader = () => {
        loader.classList.add('is-active');
        loader.setAttribute('aria-hidden', 'false');
    };

    const hideLoader = () => {
        loader.classList.remove('is-active');
        loader.setAttribute('aria-hidden', 'true');
    };

    window.addEventListener('load', hideLoader);
    window.addEventListener('pageshow', hideLoader);
    window.addEventListener('beforeunload', showLoader);

    document.querySelectorAll('a[href]').forEach(link => {
        link.addEventListener('click', function(event) {
            const href = this.getAttribute('href');
            if (
                event.defaultPrevented ||
                event.metaKey ||
                event.ctrlKey ||
                event.shiftKey ||
                event.altKey ||
                this.target === '_blank' ||
                this.hasAttribute('download') ||
                !href ||
                href.startsWith('#') ||
                href.startsWith('mailto:') ||
                href.startsWith('tel:') ||
                href.startsWith('javascript:')
            ) {
                return;
            }
            showLoader();
        });
    });

    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            if (form.checkValidity()) {
                showLoader();
            }
        });
    });
}

/**
 * Initialize animations and transitions
 */
function initializeAnimations() {
    // Observe elements for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe all cards
    document.querySelectorAll('.card').forEach(card => {
        observer.observe(card);
    });
}

/**
 * Form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

/**
 * Initialize interactive elements
 */
function initializeInteractiveElements() {
    // Add hover effects to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Add interaction to cards
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.boxShadow = '0 12px 30px rgba(0, 0, 0, 0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.08)';
        });
    });
}

/**
 * Update notification count
 */
function updateNotificationCount() {
    // Messaging notifications are only available for student accounts.
    if (document.body.dataset.userRole !== 'student') {
        return;
    }

    fetch('/messages/available-users/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .catch(error => console.log('Notification count update skipped'));
}

/**
 * Like/Unlike post via AJAX
 */
function toggleLike(postId) {
    const btn = document.querySelector(`[data-post-id="${postId}"] .like-btn`);
    
    fetch(`/posts/${postId}/like/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.liked) {
            btn.classList.add('liked');
            btn.innerHTML = '<i class="fas fa-heart text-danger"></i>';
        } else {
            btn.classList.remove('liked');
            btn.innerHTML = '<i class="far fa-heart"></i>';
        }
        // Update count
        const countEl = btn.parentElement.querySelector('.like-count');
        if (countEl) {
            countEl.textContent = data.total_likes;
        }
    })
    .catch(error => console.error('Error toggling like:', error));
}

/**
 * Get CSRF token from cookies
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Show image preview before upload
 */
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('imagePreview');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
                preview.style.animation = 'fadeIn 0.3s ease-out';
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

/**
 * Show video preview before upload
 */
function previewVideo(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('videoPreview');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
                preview.style.animation = 'fadeIn 0.3s ease-out';
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

/**
 * Delete comment via AJAX
 */
function deleteComment(commentId, postId) {
    if (confirm('Are you sure you want to delete this comment?')) {
        fetch(`/comments/${commentId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.querySelector(`[data-comment-id="${commentId}"]`).remove();
                showNotification('Comment deleted successfully', 'success');
            }
        })
        .catch(error => console.error('Error deleting comment:', error));
    }
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show m-3`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertDiv.style.animation = 'slideInDown 0.5s ease-out';
    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

/**
 * Add smooth scroll behavior
 */
function smoothScroll(target) {
    const element = document.querySelector(target);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// Export functions for global use
window.toggleLike = toggleLike;
window.previewImage = previewImage;
window.previewVideo = previewVideo;
window.deleteComment = deleteComment;
window.showNotification = showNotification;
window.smoothScroll = smoothScroll;
