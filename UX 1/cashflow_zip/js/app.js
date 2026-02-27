// ========================================
// CASHFLOW - INTERACTIVE BEHAVIORS
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initActiveNavigation();
    initAnimations();
});

// ========================================
// SIDEBAR COLLAPSIBLE SYSTEM
// ========================================

function initSidebar() {
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');
    const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
    const body = document.body;

    // Only initialize hamburger/backdrop interactions on homepage
    if (body.classList.contains('homepage')) {

        // Open sidebar — hamburger disappears via CSS (opacity:0) when sidebar-open is added
        if (hamburgerBtn) {
            hamburgerBtn.addEventListener('click', function() {
                body.classList.add('sidebar-open');
            });
        }

        // Close sidebar via the X close button
        if (sidebarCloseBtn) {
            sidebarCloseBtn.addEventListener('click', function() {
                body.classList.remove('sidebar-open');
            });
        }

        // Close sidebar by clicking the blurred backdrop (right-side empty area)
        if (sidebarBackdrop) {
            sidebarBackdrop.addEventListener('click', function() {
                body.classList.remove('sidebar-open');
            });
        }

        // Close sidebar on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && body.classList.contains('sidebar-open')) {
                body.classList.remove('sidebar-open');
            }
        });

        // Close sidebar when a nav link is clicked
        if (sidebar) {
            const navLinks = sidebar.querySelectorAll('.nav-item');
            navLinks.forEach(link => {
                link.addEventListener('click', function() {
                    setTimeout(() => {
                        body.classList.remove('sidebar-open');
                    }, 100);
                });
            });
        }
    }

    // Internal pages: sidebar auto-expands on hover (CSS handles this)
}

// ========================================
// ACTIVE NAVIGATION STATE
// ========================================

function initActiveNavigation() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.classList.remove('active');
        const href = item.getAttribute('href');
        if (href === currentPage) {
            item.classList.add('active');
        }
    });
}

// ========================================
// SCROLL ANIMATIONS
// ========================================

function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements on homepage
    const animatedElements = document.querySelectorAll('.feature-card, .step, .stat');
    animatedElements.forEach(el => observer.observe(el));
}

// ========================================
// SMOOTH SCROLL
// ========================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && href.length > 1) {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// ========================================
// UTILITY: Add loading state to buttons
// ========================================

function addButtonLoader(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinner">
            <circle cx="12" cy="12" r="10" opacity="0.25"/>
            <path d="M12 2a10 10 0 0 1 10 10" opacity="0.75"/>
        </svg>
        Loading...
    `;

    return () => {
        button.disabled = false;
        button.innerHTML = originalText;
    };
}

// Add spinner animation CSS
const style = document.createElement('style');
style.textContent = `
    .spinner {
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
