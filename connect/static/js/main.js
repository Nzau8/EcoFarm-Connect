// Dropdown menu functionality
document.addEventListener('DOMContentLoaded', function() {
    var dropdowns = document.querySelectorAll('.dropdown-toggle');
    dropdowns.forEach(function(dropdown) {
        dropdown.addEventListener('click', function(e) {
            e.preventDefault();
            var menu = this.nextElementSibling;
            menu.classList.toggle('show');
        });
    });
});

// Alert dismissal
document.addEventListener('DOMContentLoaded', function() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        var closeButton = alert.querySelector('.btn-close');
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                alert.remove();
            });
        }
    });
});

// UI Interactions
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });

    // Smooth scroll with progress indicator
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            // to change
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            if (!target) return; // Exit if target element doesn't exist

            const progressBar = document.createElement('div');
            progressBar.classList.add('scroll-progress');
            document.body.appendChild(progressBar);

            const start = window.pageYOffset;
            const end = target.offsetTop;
            const distance = end - start;
            const duration = 1000;
            let startTime = null;

            function animation(currentTime) {
                if (startTime === null) startTime = currentTime;
                const timeElapsed = currentTime - startTime;
                const progress = Math.min(timeElapsed / duration, 1);
                
                window.scrollTo(0, start + distance * easeInOutCubic(progress));
                progressBar.style.width = `${progress * 100}%`;

                if (timeElapsed < duration) {
                    requestAnimationFrame(animation);
                } else {
                    progressBar.remove();
                }
            }

            requestAnimationFrame(animation);
        });
    });

    // form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                highlightInvalidFields(form);
            }
            form.classList.add('was-validated');
        });
    });

    // Lazy loading images with blur effect
    const lazyImages = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('blur-load');
                img.onload = () => img.classList.remove('blur-load');
                observer.unobserve(img);
            }
        });
    });

    lazyImages.forEach(img => imageObserver.observe(img));
});

// Utility functions
function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
}

function highlightInvalidFields(form) {
    const invalidFields = form.querySelectorAll(':invalid');
    invalidFields.forEach(field => {
        field.parentElement.classList.add('shake-animation');
        setTimeout(() => {
            field.parentElement.classList.remove('shake-animation');
        }, 1000);
    });
}

// loading states
function showLoading(element) {
    element.classList.add('loading');
    element.setAttribute('disabled', true);
}

function hideLoading(element) {
    element.classList.remove('loading');
    element.removeAttribute('disabled');
}

// Dynamic content loading
async function loadContent(url, targetElement) {
    try {
        showLoading(targetElement);
        const response = await fetch(url);
        const data = await response.text();
        targetElement.innerHTML = data;
        targetElement.classList.add('animate-slide-in');
    } catch (error) {
        console.error('Error loading content:', error);
        targetElement.innerHTML = '<p class="text-danger">Error loading content. Please try again.</p>';
    } finally {
        hideLoading(targetElement);
    }
}

// Add animation class 
const animateOnScroll = () => {
    const elements = document.querySelectorAll('.card, .feature-icon, .testimonial-card');
    elements.forEach(element => {
        const elementTop = element.getBoundingClientRect().top;
        const elementVisible = 150;
        if (elementTop < window.innerHeight - elementVisible) {
            element.classList.add('animate-fade-in');
        }
    });
};

window.addEventListener('scroll', animateOnScroll);
window.addEventListener('load', animateOnScroll);

// Theme Switcher
function initThemeSwitcher() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.dataset.theme = document.body.dataset.theme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('theme', document.body.dataset.theme);
        });

        // Set initial theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.body.dataset.theme = savedTheme;
    }
}

//Form Validation
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                validateInput(input);
            });

            input.addEventListener('blur', () => {
                validateInput(input);
            });
        });
    });
}

function validateInput(input) {
    const errorElement = input.nextElementSibling;
    if (input.checkValidity()) {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        if (errorElement && errorElement.classList.contains('invalid-feedback')) {
            errorElement.style.display = 'none';
        }
    } else {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
        if (errorElement && errorElement.classList.contains('invalid-feedback')) {
            errorElement.style.display = 'block';
            errorElement.textContent = input.validationMessage;
        }
    }
}


function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
}

function initializeLazyLoading() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('blur-load');
                img.onload = () => img.classList.remove('blur-load');
                observer.unobserve(img);
            }
        });
    });

    lazyImages.forEach(img => imageObserver.observe(img));
}

function initializeAnimations() {
    // Initialize scroll animations
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.animate-on-scroll');
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;
            if (elementTop < window.innerHeight - elementVisible) {
                element.classList.add('animate-fade-in');
            }
        });
    };

    window.addEventListener('scroll', animateOnScroll);
    window.addEventListener('load', animateOnScroll);

    // animation classes to elements
    document.querySelectorAll('.card, .feature-icon, .testimonial-card').forEach(element => {
        element.classList.add('animate-on-scroll');
    });
}

// Initialize all features when the document is ready
document.addEventListener('DOMContentLoaded', () => {
    initThemeSwitcher();
    initFormValidation();
    initializeTooltips();
    initializeLazyLoading();
    initializeAnimations();
});

