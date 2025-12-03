(() => {
  const canvas = document.getElementById('graphCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let width = window.innerWidth;
  let height = window.innerHeight;

  const GOLD_RGB = '255, 210, 74';
  const GOLD_SOFT = 'rgba(255, 210, 74, 0.6)';

  const config = {
    particleCount: 150,
    particleSpeed: 0.5,
    connectionDistance: 180,
    interactive: true,
  };

  const mouse = { x: null, y: null, radius: 160 };

  const resize = () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  };

  window.addEventListener('resize', resize);
  resize();

  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = e.clientX - rect.left;
    mouse.y = e.clientY - rect.top;
  });

  canvas.addEventListener('mouseleave', () => {
    mouse.x = null;
    mouse.y = null;
  });

  class Particle {
    constructor() {
      this.reset();
    }

    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      const angle = Math.random() * Math.PI * 2;
      const speed = config.particleSpeed * 0.8 * (0.5 + Math.random() * 0.5);
      this.vx = Math.cos(angle) * speed;
      this.vy = Math.sin(angle) * speed;
      this.size = 2.1 + Math.random() * 2.1;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;

      if (this.x < 0 || this.x > width) this.vx *= -1;
      if (this.y < 0 || this.y > height) this.vy *= -1;

      if (config.interactive && mouse.x !== null && mouse.y !== null) {
        const dx = this.x - mouse.x;
        const dy = this.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < mouse.radius) {
          this.x += dx * 0.02;
          this.y += dy * 0.02;
        }
      }
    }

    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(252, 255, 69, 0.7)';
      ctx.fill();
    }
  }

  let particles = [];

  const initParticles = () => {
    particles = [];
    for (let i = 0; i < config.particleCount; i += 1) {
      particles.push(new Particle());
    }
  };

  const drawConnections = () => {
    for (let i = 0; i < particles.length; i += 1) {
      for (let j = i + 1; j < particles.length; j += 1) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < config.connectionDistance) {
          const opacity = Math.max(0, Math.min(100, (1 - dist / config.connectionDistance) * 0.529));
          ctx.strokeStyle = `rgba(${GOLD_RGB}, ${opacity})`;
          ctx.lineWidth = 0.6;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }
  };

  const animate = () => {
    ctx.clearRect(0, 0, width, height);

    particles.forEach((p) => {
      p.update();
      p.draw();
    });

    drawConnections();
    requestAnimationFrame(animate);
  };

  initParticles();
  animate();
})();
