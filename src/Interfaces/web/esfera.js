let escena, camara, render, redNeuronal, nodosSinapticos, brilloNucleo;
let estadoActual = "ESPERA";
let colorObjetivo = new THREE.Color("#0077ff"); // Variable maestra de control de color
let velocidadGiro = 0.005;
let deltaTiempo = 0;
let amplitudOnda = 0.03;

function inicializarEsfera() {
    const contenedor = document.getElementById('canvas-container');
    
    escena = new THREE.Scene();
    escena.fog = new THREE.FogExp2(0x04040a, 0.08);

    camara = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camara.position.z = 7.0;

    render = new THREE.WebGLRenderer({ antialias: true });
    render.setSize(window.innerWidth, window.innerHeight);
    render.setPixelRatio(window.devicePixelRatio);
    contenedor.appendChild(render.domElement);

    const geometriaEsfera = new THREE.IcosahedronGeometry(2.1, 3);
    geometriaEsfera.userData = {
        posOriginales: geometriaEsfera.attributes.position.clone()
    };

    // 🎯 MEJORADO: Vinculamos el color inicial directamente a la referencia dinámica
    const matLineas = new THREE.MeshBasicMaterial({
        color: colorObjetivo, 
        wireframe: true,
        transparent: true,
        opacity: 0.4
    });
    redNeuronal = new THREE.Mesh(geometriaEsfera, matLineas);
    escena.add(redNeuronal);

    const matPuntos = new THREE.PointsMaterial({
        color: colorObjetivo, 
        size: 0.07,
        transparent: true,
        opacity: 0.9
    });
    nodosSinapticos = new THREE.Points(geometriaEsfera, matPuntos);
    escena.add(nodosSinapticos);

    const geoBrillo = new THREE.SphereGeometry(0.8, 16, 16);
    const matBrillo = new THREE.MeshBasicMaterial({
        color: colorObjetivo, 
        transparent: true,
        opacity: 0.15,
        blending: THREE.AdditiveBlending
    });
    brilloNucleo = new THREE.Mesh(geoBrillo, matBrillo);
    escena.add(brilloNucleo);

    generarPolvoCosmico();
    window.addEventListener('resize', enRedimension, false);
    
    bucleAnimacion();
    conectarServidorCore();
}

function generarPolvoCosmico() {
    const geoFondo = new THREE.BufferGeometry();
    const cantidad = 200;
    const posiciones = new Float32Array(cantidad * 3);

    for(let i=0; i < cantidad*3; i+=3) {
        posiciones[i] = (Math.random() - 0.5) * 15;
        posiciones[i+1] = (Math.random() - 0.5) * 15;
        posiciones[i+2] = (Math.random() - 0.5) * 15;
    }
    geoFondo.setAttribute('position', new THREE.BufferAttribute(posiciones, 3));
    const matFondo = new THREE.PointsMaterial({ 
        color: 0xffffff, 
        size: 0.03, 
        transparent: true, 
        opacity: 0.3,
        blending: THREE.AdditiveBlending
    });
    const nubeFondo = new THREE.Points(geoFondo, matFondo);
    escena.add(nubeFondo);
}

function conectarServidorCore() {
    const socket = new WebSocket("ws://127.0.0.1:8000/ws");
    const hudTexto = document.getElementById("status-text");
    const hudContenedor = document.getElementById("hud-banner");

    socket.onmessage = function(evento) {
        const comando = JSON.parse(evento.data);
        estadoActual = comando.estado;
        
        // Asignación de mutaciones cromáticas y comportamiento físico
        if (estadoActual === "ESCUCHANDO") {
            colorObjetivo.set("#00ffcc"); // Cian Eléctrico
            velocidadGiro = 0.015;
            amplitudOnda = 0.15;
        } else if (estadoActual === "PENSANDO") {
            colorObjetivo.set("#ffaa00"); // Ámbar / Dorado cuántico
            velocidadGiro = 0.06;
            amplitudOnda = 0.05;
        } else if (estadoActual === "HABLANDO") {
            colorObjetivo.set("#ff0055"); // Fucsia de alta frecuencia
            velocidadGiro = 0.008;
            amplitudOnda = 0.35;
        } else {
            colorObjetivo.set("#0077ff"); // Azul estándar
            velocidadGiro = 0.004;
            amplitudOnda = 0.03;
        }

        // Modificación del entorno CSS HUD en tiempo de ejecución
        hudTexto.innerText = `REVAN V1.0 | ${comando.estado}`;
        hudTexto.style.color = colorObjetivo.getStyle();
        hudContenedor.style.borderColor = colorObjetivo.getStyle();
        hudContenedor.style.boxShadow = `0 0 30px ${colorObjetivo.getStyle()}44, inset 0 0 15px ${colorObjetivo.getStyle()}11`;
    };

    socket.onclose = function() {
        setTimeout(conectarServidorCore, 2000);
    };
}

function bucleAnimacion() {
    requestAnimationFrame(bucleAnimacion);
    deltaTiempo += (estadoActual === "PENSANDO") ? 0.25 : 0.05;

    // MEJORADO: Interpolación lineal explícita por cuadro en la GPU para transiciones líquidas
    redNeuronal.material.color.lerp(colorObjetivo, 0.08);
    nodosSinapticos.material.color.lerp(colorObjetivo, 0.08);
    brilloNucleo.material.color.lerp(colorObjetivo, 0.08);

    // Forzado de banderas internas de actualización para Three.js
    redNeuronal.material.needsUpdate = true;
    nodosSinapticos.material.needsUpdate = true;
    brilloNucleo.material.needsUpdate = true;

    redNeuronal.rotation.y += velocidadGiro;
    redNeuronal.rotation.x += velocidadGiro * 0.3;
    nodosSinapticos.rotation.y = redNeuronal.rotation.y;
    nodosSinapticos.rotation.x = redNeuronal.rotation.x;

    const posAttr = redNeuronal.geometry.attributes.position;
    const posOrig = redNeuronal.geometry.userData.posOriginales;
    
    for (let i = 0; i < posAttr.count; i++) {
        let x = posOrig.getX(i);
        let y = posOrig.getY(i);
        let z = posOrig.getZ(i);

        let factorOnda = Math.sin(x * 1.5 + deltaTiempo) * Math.cos(y * 1.5 + deltaTiempo) * Math.sin(z * 1.0 + deltaTiempo);
        let desplazamiento = 1.0 + factorOnda * amplitudOnda;

        posAttr.setXYZ(i, x * desplazamiento, y * desplazamiento, z * desplazamiento);
    }
    posAttr.needsUpdate = true;

    let escalaBrillo = 1.0 + Math.sin(deltaTiempo * 2) * 0.1;
    brilloNucleo.scale.set(escalaBrillo, escalaBrillo, escalaBrillo);

    render.render(escena, camara);
}

function enRedimension() {
    camara.aspect = window.innerWidth / window.innerHeight;
    camara.updateProjectionMatrix();
    render.setSize(window.innerWidth, window.innerHeight);
}

window.onload = inicializarEsfera;