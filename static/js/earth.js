import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.153.0/build/three.module.js';

window.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('earth-container');
    if (!container) {
        console.error('Элемент #earth-container не найден!');
        return;
    }

    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 3;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);

    const geometry = new THREE.SphereGeometry(1, 64, 64);
    const textureLoader = new THREE.TextureLoader();
    const texture = textureLoader.load('https://threejs.org/examples/textures/earth_atmos_2048.jpg');
    const material = new THREE.MeshStandardMaterial({ map: texture });
    const earth = new THREE.Mesh(geometry, material);
    scene.add(earth);

    const ambientLight = new THREE.AmbientLight(0xffffff, 1);
    scene.add(ambientLight);

    function animate() {
        requestAnimationFrame(animate);
        earth.rotation.y += 0.0015;
        renderer.render(scene, camera);
    }

    animate();

    window.addEventListener('resize', () => {
        const width = container.clientWidth;
        const height = container.clientHeight;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    });
});
