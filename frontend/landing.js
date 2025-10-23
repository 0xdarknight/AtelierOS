const canvas = document.getElementById('fabric-canvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

class FabricThread {
    constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.length = Math.random() * 150 + 60;
        this.angle = Math.random() * Math.PI * 2;
        this.opacity = Math.random() * 0.06 + 0.01;
        this.speed = Math.random() * 0.15 + 0.03;
        this.color = `rgba(155, 143, 130, ${this.opacity})`;
    }

    update() {
        this.y += this.speed;
        if (this.y > canvas.height + this.length) {
            this.y = -this.length;
            this.x = Math.random() * canvas.width;
        }
    }

    draw() {
        ctx.beginPath();
        ctx.moveTo(this.x, this.y);
        ctx.lineTo(
            this.x + Math.cos(this.angle) * this.length,
            this.y + Math.sin(this.angle) * this.length
        );
        ctx.strokeStyle = this.color;
        ctx.lineWidth = 1;
        ctx.stroke();
    }
}

const threads = [];
for (let i = 0; i < 250; i++) {
    threads.push(new FabricThread());
}

function animateFabric() {
    ctx.fillStyle = 'rgba(248, 246, 241, 0.02)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    threads.forEach(thread => {
        thread.update();
        thread.draw();
    });
    requestAnimationFrame(animateFabric);
}

animateFabric();

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

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

window.addEventListener('scroll', () => {
    const nav = document.querySelector('.nav');
    if (window.scrollY > 50) {
        nav.style.background = 'rgba(248, 246, 241, 0.98)';
    } else {
        nav.style.background = 'rgba(248, 246, 241, 0.95)';
    }
});

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.agent-showcase, .capability, .tech-item').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'all 0.6s ease';
    observer.observe(el);
});
