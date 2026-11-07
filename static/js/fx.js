/* Effets visuels légers : un seul canvas, une boucle rAF qui s'arrête quand il n'y a plus de particules. */
const TeaFX = (() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const MAX_PARTICLES = 420;

    let canvas = null;
    let ctx = null;
    let flashEl = null;
    let particles = [];
    let frame = 0;
    let last = 0;
    let dpr = 1;

    function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.round(window.innerWidth * dpr);
        canvas.height = Math.round(window.innerHeight * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function ensureCanvas() {
        if (canvas) return;
        canvas = document.createElement("canvas");
        canvas.className = "fx-canvas";
        canvas.setAttribute("aria-hidden", "true");
        document.body.appendChild(canvas);
        ctx = canvas.getContext("2d");
        resize();
        window.addEventListener("resize", resize, { passive: true });
    }

    function tick(now) {
        const dt = Math.min((now - last) / 1000, 0.05);
        last = now;
        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
        ctx.globalCompositeOperation = "lighter";

        particles = particles.filter(p => (p.age += dt) < p.life);
        for (const p of particles) {
            p.vy += p.gravity * dt;
            p.vx *= 1 - 1.6 * dt;
            p.vy *= 1 - 1.2 * dt;
            p.x += p.vx * dt;
            p.y += p.vy * dt;

            const t = p.age / p.life;
            ctx.globalAlpha = (1 - t) * (1 - t);
            ctx.fillStyle = p.color;
            ctx.strokeStyle = p.color;

            if (p.spark) {
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p.x - p.vx * 0.04, p.y - p.vy * 0.04);
                ctx.stroke();
            } else {
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size * (1 - t * 0.5), 0, Math.PI * 2);
                ctx.fill();
            }
        }
        ctx.globalAlpha = 1;

        if (particles.length) {
            frame = requestAnimationFrame(tick);
        } else {
            frame = 0;
            ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
        }
    }

    function burst(x, y, color, count = 40, power = 1) {
        if (reduceMotion) return;
        ensureCanvas();
        for (let i = 0; i < count && particles.length < MAX_PARTICLES; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = (120 + Math.random() * 520) * power;
            particles.push({
                x, y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed - 80 * power,
                gravity: 260,
                size: 1.5 + Math.random() * 3.5,
                life: 0.7 + Math.random() * 0.9,
                age: 0,
                color,
                spark: Math.random() < 0.35
            });
        }
        if (!frame) {
            last = performance.now();
            frame = requestAnimationFrame(tick);
        }
    }

    function flash(color, strength = 0.5) {
        if (reduceMotion || !window.gsap) return;
        if (!flashEl) {
            flashEl = document.createElement("div");
            flashEl.className = "fx-flash";
            flashEl.setAttribute("aria-hidden", "true");
            document.body.appendChild(flashEl);
        }
        flashEl.style.setProperty("--fc", color);
        gsap.fromTo(flashEl, { opacity: strength }, { opacity: 0, duration: 0.55, ease: "power2.out" });
    }

    function shake(element, intensity = 8) {
        if (reduceMotion || !window.gsap) return;
        gsap.fromTo(element,
            { x: -intensity },
            { x: 0, duration: 0.5, ease: "elastic.out(1.2, 0.2)", clearProps: "x" });
    }

    return { burst, flash, shake, reduceMotion };
})();
