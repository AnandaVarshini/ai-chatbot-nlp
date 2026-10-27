// ============================================================
// API Configuration
// ============================================================
const API_URL = 'http://127.0.0.1:8080';

// ============================================================
// 3D Particle Background (Three.js)
// ============================================================
function initParticles() {
    const container = document.createElement('div');
    container.id = 'particles-js';
    document.body.prepend(container);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 2000;
    const posArray = new Float32Array(particlesCount * 3);
    const colorArray = new Float32Array(particlesCount * 3);
    for (let i = 0; i < particlesCount * 3; i += 3) {
        posArray[i] = (Math.random() - 0.5) * 30;
        posArray[i + 1] = (Math.random() - 0.5) * 20;
        posArray[i + 2] = (Math.random() - 0.5) * 30;
        const color = new THREE.Color();
        color.setHSL(0.7 + Math.random() * 0.2, 0.8, 0.5 + Math.random() * 0.3);
        colorArray[i] = color.r;
        colorArray[i + 1] = color.g;
        colorArray[i + 2] = color.b;
    }
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));
    const particlesMaterial = new THREE.PointsMaterial({
        size: 0.05,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending,
        sizeAttenuation: true,
    });
    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particlesMesh);
    let mouseX = 0;
    let mouseY = 0;
    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX / window.innerWidth) * 2 - 1;
        mouseY = -(event.clientY / window.innerHeight) * 2 + 1;
    });
    let time = 0;
    function animate() {
        requestAnimationFrame(animate);
        time += 0.001;
        particlesMesh.rotation.y += 0.0005;
        particlesMesh.rotation.x += 0.0002;
        particlesMesh.rotation.x += (mouseY * 0.02 - particlesMesh.rotation.x) * 0.005;
        particlesMesh.rotation.y += (mouseX * 0.02 - particlesMesh.rotation.y) * 0.005;
        const scale = 1 + Math.sin(time * 2) * 0.02;
        particlesMesh.scale.set(scale, scale, scale);
        renderer.render(scene, camera);
    }
    animate();
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

// ============================================================
// Custom 3D Cursor
// ============================================================
function initCursor() {
    const cursorGlow = document.createElement('div');
    cursorGlow.className = 'cursor-glow';
    document.body.appendChild(cursorGlow);
    const cursorDot = document.createElement('div');
    cursorDot.className = 'cursor-dot';
    document.body.appendChild(cursorDot);
    let mouseX = 0;
    let mouseY = 0;
    let glowX = 0;
    let glowY = 0;
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });
    function animateCursor() {
        requestAnimationFrame(animateCursor);
        glowX += (mouseX - glowX) * 0.08;
        glowY += (mouseY - glowY) * 0.08;
        cursorDot.style.left = mouseX + 'px';
        cursorDot.style.top = mouseY + 'px';
        cursorGlow.style.left = glowX + 'px';
        cursorGlow.style.top = glowY + 'px';
    }
    animateCursor();
    const interactiveElements = document.querySelectorAll('button, input, .quick-btn, .send-btn');
    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursorDot.classList.add('hover');
            cursorGlow.style.width = '300px';
            cursorGlow.style.height = '300px';
        });
        el.addEventListener('mouseleave', () => {
            cursorDot.classList.remove('hover');
            cursorGlow.style.width = '200px';
            cursorGlow.style.height = '200px';
        });
    });
}

// ============================================================
// Initialize Everything (chat logic is in index.html)
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initCursor();
});
