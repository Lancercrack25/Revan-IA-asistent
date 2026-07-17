let escena, camara, render, redNeuronal, nodosSinapticos, brilloNucleo;
let estadoActual = "ESPERA";
let colorObjetivo = new THREE.Color("#0077ff"); // Variable maestra de control de color
let velocidadGiro = 0.005;
let deltaTiempo = 0;
let amplitudOnda = 0.03;
let manoActiva = false;
let rotXObjetivo = 0;
let rotYObjetivo = 0;
let escalaObjetivo = 1.0;
let ultimaManipulacionTs = 0;
const TIMEOUT_MANO_MS = 500;
const SUAVIZADO_MANO = 0.15; // 0 = no se mueve, 1 = salto instantáneo sin suavizar

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

        if (comando.tipo === "manipulacion") {
            rotXObjetivo = comando.rotX;
            rotYObjetivo = comando.rotY;
            escalaObjetivo = comando.escala;
            manoActiva = true;
            ultimaManipulacionTs = Date.now();
            return; // no tocar el estado/color, este paquete no trae eso
        }

        // Paquete de estado normal (con o sin "tipo": "estado", por si
        // llega un paquete viejo sin el campo, sigue funcionando igual)
        estadoActual = comando.estado;
        
        // 🎯 FIX: Normalizamos el nombre del estado (Acepta tanto PENSANDO como PROCESANDO)
        if (estadoActual === "ESCUCHANDO") {
            colorObjetivo.set(comando.color || "#00ffcc"); // Cian / Azul claro
            velocidadGiro = 0.015;
            amplitudOnda = 0.15;
        } else if (estadoActual === "PENSANDO" || estadoActual === "PROCESANDO") {
            colorObjetivo.set(comando.color || "#ffaa00"); // Ámbar / Dorado cuántico
            velocidadGiro = 0.06;
            amplitudOnda = 0.05;
        } else if (estadoActual === "HABLANDO") {
            colorObjetivo.set(comando.color || "#ff0055"); // Fucsia / Rojo
            velocidadGiro = 0.008;
            amplitudOnda = 0.35;
        } else {
            colorObjetivo.set(comando.color || "#0077ff"); // Azul estándar (ESPERA)
            velocidadGiro = 0.004;
            amplitudOnda = 0.03;
        }

        // Modificación del entorno CSS HUD en tiempo de ejecución (Verificando existencia de elementos)
        if (hudTexto) {
            hudTexto.innerText = `REVAN V1.0 | ${estadoActual}`;
            hudTexto.style.color = colorObjetivo.getStyle();
        }
        if (hudContenedor) {
            hudContenedor.style.borderColor = colorObjetivo.getStyle();
            hudContenedor.style.boxShadow = `0 0 30px ${colorObjetivo.getStyle()}44, inset 0 0 15px ${colorObjetivo.getStyle()}11`;
        }
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

    // ─── NUEVO: si no ha llegado un paquete de manipulación reciente,
    // se considera que la mano ya no está frente a la cámara, y se vuelve
    // al giro automático de siempre.
    if (manoActiva && (Date.now() - ultimaManipulacionTs > TIMEOUT_MANO_MS)) {
        manoActiva = false;
    }

    if (manoActiva) {
        // Control directo: la rotación sigue tu mano en vez del giro automático
        redNeuronal.rotation.x += (rotXObjetivo - redNeuronal.rotation.x) * SUAVIZADO_MANO;
        redNeuronal.rotation.y += (rotYObjetivo - redNeuronal.rotation.y) * SUAVIZADO_MANO;

        const escalaActual = redNeuronal.scale.x;
        const nuevaEscala = escalaActual + (escalaObjetivo - escalaActual) * SUAVIZADO_MANO;
        redNeuronal.scale.set(nuevaEscala, nuevaEscala, nuevaEscala);
        nodosSinapticos.scale.set(nuevaEscala, nuevaEscala, nuevaEscala);
    } else {
        // Comportamiento original: giro automático constante
        redNeuronal.rotation.y += velocidadGiro;
        redNeuronal.rotation.x += velocidadGiro * 0.3;

        // Devolver la escala manual a su tamaño normal si se soltó la mano
        const escalaActual = redNeuronal.scale.x;
        if (Math.abs(escalaActual - 1.0) > 0.001) {
            const nuevaEscala = escalaActual + (1.0 - escalaActual) * SUAVIZADO_MANO;
            redNeuronal.scale.set(nuevaEscala, nuevaEscala, nuevaEscala);
            nodosSinapticos.scale.set(nuevaEscala, nuevaEscala, nuevaEscala);
        }
    }

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