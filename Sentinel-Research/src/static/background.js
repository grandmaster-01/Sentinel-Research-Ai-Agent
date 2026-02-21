// 3D Particle Network Configuration
document.addEventListener('DOMContentLoaded', () => {
    const canvasContainer = document.querySelector('.background-globes');

    // Remove old CSS globes if they exist to clear way for Canvas
    canvasContainer.innerHTML = '';
    canvasContainer.style.background = 'radial-gradient(circle at center, var(--bg-color), #000)';

    // Scene Setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    canvasContainer.appendChild(renderer.domElement);

    // Particles Setup
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 700; // Adjust for density

    const posArray = new Float32Array(particlesCount * 3);

    for (let i = 0; i < particlesCount * 3; i++) {
        // Spread particles across a wide space
        posArray[i] = (Math.random() - 0.5) * 25;
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

    // Material
    const material = new THREE.PointsMaterial({
        size: 0.02,
        color: 0x3b82f6, // Accent color match
        transparent: true,
        opacity: 0.8,
    });

    // Mesh
    const particlesMesh = new THREE.Points(particlesGeometry, material);
    scene.add(particlesMesh);

    // Connect particles with lines (Optional, computationally expensive)
    // stick to just particles/stars for performance but add movement

    camera.position.z = 5;

    // Interaction
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const windowHalfX = window.innerWidth / 2;
    const windowHalfY = window.innerHeight / 2;

    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX - windowHalfX);
        mouseY = (event.clientY - windowHalfY);
    });

    // Theme Listener
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.attributeName === 'data-theme') {
                const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
                material.color.setHex(isDark ? 0x3b82f6 : 0x2563eb);
                material.opacity = isDark ? 0.8 : 0.6;
            }
        });
    });

    observer.observe(document.documentElement, { attributes: true });

    // Animation Loop
    const clock = new THREE.Clock();

    const animate = () => {
        targetX = mouseX * 0.001;
        targetY = mouseY * 0.001;

        particlesMesh.rotation.y += 0.002;
        particlesMesh.rotation.x += 0.001; // Constant rotation

        // Mouse interaction easing
        particlesMesh.rotation.y += 0.05 * (targetX - particlesMesh.rotation.y);
        particlesMesh.rotation.x += 0.05 * (targetY - particlesMesh.rotation.x);

        renderer.render(scene, camera);
        requestAnimationFrame(animate);
    };

    animate();

    // Resize Handle
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
});
