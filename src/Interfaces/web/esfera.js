let escena, camara, render, redNeuronal, nodosSinapticos, brilloNucleo;
let estadoActual = "ESPERA";
let colorObjetivo = new THREE.Color("#0077ff"); // Variable maestra de control de color
let velocidadGiro = 0.005;
let deltaTiempo = 0;
let amplitudOnda = 0.03;

// Control Táctil / Mano (Tracking)
let manoActiva = false;
let rotXObjetivo = 0;
let rotYObjetivo = 0;
let escalaObjetivo = 1.0;
let ultimaManipulacionTs = 0;
const TIMEOUT_MANO_MS = 500;
const SUAVIZADO_MANO = 0.15; // 0 = sin movimiento, 1 = instantáneo

function inicializarEsfera() {
    const contenedor = document.getElementById('canvas-container');
    if (!contenedor) return;

    // 1. Escena y Niebla Deep Space
    escena = new THREE.Scene();
    escena.fog = new THREE.FogExp2(0x04040a, 0.08);

    // 2. Cámara
    camara = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camara.position.z = 7.0;

    // 3. Renderizador WebGL
    render = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    render.setSize(window.innerWidth, window.innerHeight);
    render.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    contenedor.appendChild(render.domElement);

    // 4. Geometría Compartida (Red Neuronal + Nodos)
    const geometriaEsfera = new THREE.IcosahedronGeometry(2.1, 3);
    geometriaEsfera.userData = {
        posOriginales: geometriaEsfera.attributes.position.clone()
    };

    // Material de Malla Wireframe
    const matLineas = new THREE.MeshBasicMaterial({
        color: colorObjetivo, 
        wireframe: true,
        transparent: true,
        opacity: 0.4
    });
    redNeuronal = new THREE.Mesh(geometriaEsfera, matLineas);
    escena.add(redNeuronal);

    // Material de Puntos Sinápticos (Comparte geometría para sincronizar la deformación)
    const matPuntos = new THREE.PointsMaterial({
        color: colorObjetivo, 
        size: 0.07,
        transparent: true,
        opacity: 0.9
    });
    nodosSinapticos = new THREE.Points(geometriaEsfera, matPuntos);
    escena.add(nodosSinapticos);

    // 5. Núcleo Interno Sólido
    const geoBrillo = new THREE.SphereGeometry(0.8, 16, 16);
    const matBrillo = new THREE.MeshBasicMaterial({
        color: colorObjetivo, 
        transparent: true,
        opacity: 0.25,
        blending: THREE.AdditiveBlending
    });
    brilloNucleo = new THREE.Mesh(geoBrillo, matBrillo);
    escena.add(brilloNucleo);

    // Ambientación
    generarPolvoCosmico();
    
    // Listeners
    window.addEventListener('resize', enRedimension, false);
    
    // Iniciar Bucle y Conexión
    bucleAnimacion();
    conectarServidorCore();
}

function generarPolvoCosmico() {
    const geoFondo = new THREE.BufferGeometry();
    const cantidad = 250;
    const posiciones = new Float32Array(cantidad * 3);

    for(let i = 0; i < cantidad * 3; i += 3) {
        posiciones[i] = (Math.random() - 0.5) * 16;
        posiciones[i+1] = (Math.random() - 0.5) * 16;
        posiciones[i+2] = (Math.random() - 0.5) * 16;
    }

    geoFondo.setAttribute('position', new THREE.BufferAttribute(posiciones, 3));
    const matFondo = new THREE.PointsMaterial({ 
        color: 0xffffff, 
        size: 0.03, 
        transparent: true, 
        opacity: 0.35,
        blending: THREE.AdditiveBlending
    });
    const nubeFondo = new THREE.Points(geoFondo, matFondo);
    escena.add(nubeFondo);
}

function conectarServidorCore() {
    // Antes: URL fija "ws://127.0.0.1:8000/ws". Los otros 3 archivos JS
    // (dashboard.js, coder.js, creative.js) ya arman la URL dinámicamente
    // desde window.location.host -si el puerto de servidor.py cambia
    // algún día, esos tres siguen funcionando y este se rompe en silencio-.
    // Se unifica al mismo patrón.
    const socket = new WebSocket(`ws://${window.location.host}/ws`);
    const hudTexto = document.getElementById("status-text");
    const hudContenedor = document.getElementById("hud-banner");

    socket.onmessage = function(evento) {
        try {
            const comando = JSON.parse(evento.data);

            if (comando.tipo === "manipulacion") {
                rotXObjetivo = comando.rotX;
                rotYObjetivo = comando.rotY;
                escalaObjetivo = comando.escala;
                manoActiva = true;
                ultimaManipulacionTs = Date.now();
                return;
            }

            // Actualización de estado del sistema
            estadoActual = comando.estado || "ESPERA";
            
            if (estadoActual === "ESCUCHANDO") {
                colorObjetivo.set(comando.color || "#00ffcc");
                velocidadGiro = 0.015;
                amplitudOnda = 0.15;
            } else if (estadoActual === "PENSANDO" || estadoActual === "PROCESANDO") {
                colorObjetivo.set(comando.color || "#ffaa00");
                velocidadGiro = 0.06;
                amplitudOnda = 0.05;
            } else if (estadoActual === "HABLANDO") {
                colorObjetivo.set(comando.color || "#ff0055");
                velocidadGiro = 0.008;
                amplitudOnda = 0.35;
            } else {
                colorObjetivo.set(comando.color || "#0077ff");
                velocidadGiro = 0.004;
                amplitudOnda = 0.03;
            }

            // Actualización dinámica del HUD
            if (hudTexto) {
                hudTexto.innerText = `REVAN V1.0 | ${estadoActual}`;
                hudTexto.style.color = colorObjetivo.getStyle();
            }
            if (hudContenedor) {
                hudContenedor.style.borderColor = colorObjetivo.getStyle();
                hudContenedor.style.boxShadow = `0 0 30px ${colorObjetivo.getStyle()}44, inset 0 0 15px ${colorObjetivo.getStyle()}11`;
            }
        } catch (e) {
            console.error("Error procesando paquete WebSocket:", e);
        }
    };

    socket.onclose = function() {
        // Intento de reconexión automática
        setTimeout(conectarServidorCore, 2000);
    };

    socket.onerror = function() {
        socket.close();
    };
}

function bucleAnimacion() {
    requestAnimationFrame(bucleAnimacion);
    deltaTiempo += (estadoActual === "PENSANDO" || estadoActual === "PROCESANDO") ? 0.25 : 0.05;

    // Interpolación de color suave (LERP)
    redNeuronal.material.color.lerp(colorObjetivo, 0.08);
    nodosSinapticos.material.color.lerp(colorObjetivo, 0.08);
    brilloNucleo.material.color.lerp(colorObjetivo, 0.08);

    // Verificación de timeout para control gestual
    if (manoActiva && (Date.now() - ultimaManipulacionTs > TIMEOUT_MANO_MS)) {
        manoActiva = false;
    }

    if (manoActiva) {
        // Rotación guiada por manos
        redNeuronal.rotation.x += (rotXObjetivo - redNeuronal.rotation.x) * SUAVIZADO_MANO;
        redNeuronal.rotation.y += (rotYObjetivo - redNeuronal.rotation.y) * SUAVIZADO_MANO;

        const escalaActual = redNeuronal.scale.x;
        const nuevaEscala = escalaActual + (escalaObjetivo - escalaActual) * SUAVIZADO_MANO;
        redNeuronal.scale.set(nuevaEscala, nuevaEscala, nuevaEscala);
        nodosSinapticos.scale.set(nuevaEscala, nuevaEscala, nuevaEscala);
    } else {
        // Giro libre automático
        redNeuronal.rotation.y += velocidadGiro;
        redNeuronal.rotation.x += velocidadGiro * 0.3;

        // Reset de escala suave
        const escalaActual = redNeuronal.scale.x;
        if (Math.abs(escalaActual - 1.0) > 0.001) {
            const nuevaEscala = escalaActual + (1.0 - escalaActual) * SUAVIZADO_MANO;
            redNeuronal.scale.set(nuevaEscala, nuevaEscala, nuevaEscala);
            nodosSinapticos.scale.set(nuevaEscala, nuevaEscala, nuevaEscala);
        }
    }

    // Sincronizar rotaciones
    nodosSinapticos.rotation.y = redNeuronal.rotation.y;
    nodosSinapticos.rotation.x = redNeuronal.rotation.x;
    // Deformación Orgánica de Vértices
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

    // Pulsación del núcleo central
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