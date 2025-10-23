// ATELIER OS - Runway Landing Experience

// Intersection Observer for scroll-triggered animations
const observerOptions = {
    threshold: 0.2,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('in-view');
        }
    });
}, observerOptions);

// Observe all pieces (agents)
document.querySelectorAll('.piece').forEach((piece, index) => {
    piece.style.transitionDelay = `${index * 0.15}s`;
    observer.observe(piece);
});

// Smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Parallax effect on scroll
let ticking = false;

function updateParallax() {
    const scrolled = window.pageYOffset;

    // Move spotlight scanner
    const spotlight = document.querySelector('.spotlight-scanner');
    if (spotlight) {
        spotlight.style.transform = `translateY(${scrolled * 0.3}px)`;
    }

    // Subtle parallax on grid
    const grid = document.querySelector('.fashion-grid');
    if (grid) {
        grid.style.transform = `translateY(${scrolled * 0.1}px)`;
    }

    ticking = false;
}

window.addEventListener('scroll', () => {
    if (!ticking) {
        window.requestAnimationFrame(updateParallax);
        ticking = true;
    }
});

// Add entrance animation class to body
window.addEventListener('load', () => {
    document.body.classList.add('loaded');
});
