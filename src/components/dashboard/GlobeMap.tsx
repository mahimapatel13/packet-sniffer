import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as THREE from 'three';
import { GeoPointDTO } from '@/services/types';

interface GlobeMapProps {
  points: GeoPointDTO[];
}

interface TooltipData {
  ip: string;
  location: string;
  count: number;
  direction: 'source' | 'destination';
  x: number;
  y: number;
}

function latLngToVec3(lat: number, lng: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
}

export function GlobeMap({ points }: GlobeMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mountRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  const [autoRotate, setAutoRotate] = useState(true);
  const [showArcs, setShowArcs] = useState(true);
  const [showAtmosphere, setShowAtmosphere] = useState(true);

  // Refs for animation and Three.js objects
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const groupRef = useRef<THREE.Group | null>(null);
  const pointsGroupRef = useRef<THREE.Group | null>(null);
  const arcsGroupRef = useRef<THREE.Group | null>(null);
  const atmosphereGroupRef = useRef<THREE.Group | null>(null);
  const animFrameRef = useRef<number>(0);
  
  // Interaction state
  const isDraggingRef = useRef(false);
  const previousMousePositionRef = useRef({ x: 0, y: 0 });
  const rotationVelocityRef = useRef({ x: 0, y: 0 });
  const lastInteractTimeRef = useRef(Date.now());
  const autoRotateRef = useRef(true);
  const showArcsRef = useRef(true);
  
  const dotMeshesRef = useRef<{ mesh: THREE.Mesh; data: GeoPointDTO }[]>([]);
  const particlesRef = useRef<{ mesh: THREE.Mesh; curve: THREE.QuadraticBezierCurve3; progress: number; speed: number }[]>([]);
  const ringsRef = useRef<THREE.Mesh[]>([]);

  useEffect(() => {
    autoRotateRef.current = autoRotate;
  }, [autoRotate]);

  useEffect(() => {
    showArcsRef.current = showArcs;
    if (arcsGroupRef.current) {
      arcsGroupRef.current.visible = showArcs;
    }
  }, [showArcs]);

  useEffect(() => {
    if (atmosphereGroupRef.current) {
      atmosphereGroupRef.current.visible = showAtmosphere;
    }
  }, [showAtmosphere]);

  // Initial setup
  useEffect(() => {
    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = 560;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.setClearColor(0x060c18);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Scene
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 2.8);
    cameraRef.current = camera;

    // Groups
    const mainGroup = new THREE.Group();
    scene.add(mainGroup);
    groupRef.current = mainGroup;

    const pointsGroup = new THREE.Group();
    mainGroup.add(pointsGroup);
    pointsGroupRef.current = pointsGroup;

    const arcsGroup = new THREE.Group();
    mainGroup.add(arcsGroup);
    arcsGroupRef.current = arcsGroup;

    const atmosphereGroup = new THREE.Group();
    mainGroup.add(atmosphereGroup);
    atmosphereGroupRef.current = atmosphereGroup;

    // Globe layers
    // Earth sphere
    const earthGeo = new THREE.SphereGeometry(1, 64, 64);
    const earthMat = new THREE.MeshPhongMaterial({
      color: 0x0a1628,
      emissive: 0x061020,
      specular: 0x223366,
      shininess: 8
    });
    const earth = new THREE.Mesh(earthGeo, earthMat);
    mainGroup.add(earth);

    // Grid overlay
    const gridGeo = new THREE.SphereGeometry(1.002, 24, 16);
    const gridMat = new THREE.MeshBasicMaterial({
      color: 0x1a2844,
      wireframe: true,
      transparent: true,
      opacity: 0.15
    });
    const grid = new THREE.Mesh(gridGeo, gridMat);
    mainGroup.add(grid);

    // Atmosphere
    const atmoGeo = new THREE.SphereGeometry(1.06, 32, 32);
    const atmoMat = new THREE.MeshPhongMaterial({
      color: 0x1a3a6a,
      transparent: true,
      opacity: 0.15,
      side: THREE.FrontSide
    });
    const atmo = new THREE.Mesh(atmoGeo, atmoMat);
    atmosphereGroup.add(atmo);

    // Outer glow
    const glowGeo = new THREE.SphereGeometry(1.14, 32, 32);
    const glowMat = new THREE.MeshBasicMaterial({
      color: 0x0a1e3a,
      transparent: true,
      opacity: 0.06,
      side: THREE.BackSide
    });
    const glow = new THREE.Mesh(glowGeo, glowMat);
    atmosphereGroup.add(glow);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x223355, 0.6);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x6688cc, 1.2);
    dirLight1.position.set(5, 3, 5);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x334466, 0.4);
    dirLight2.position.set(-5, -2, -3);
    scene.add(dirLight2);

    // Host machine dot (India: 20.59, 78.96)
    const hostPos = latLngToVec3(20.59, 78.96, 1.013);
    const hostGeo = new THREE.SphereGeometry(0.016, 8, 8);
    const hostMat = new THREE.MeshBasicMaterial({ color: 0x60aaff });
    const hostDot = new THREE.Mesh(hostGeo, hostMat);
    hostDot.position.copy(hostPos);
    mainGroup.add(hostDot);

    const hostRingGeo = new THREE.RingGeometry(0.028, 0.038, 16);
    const hostRingMat = new THREE.MeshBasicMaterial({ color: 0x60aaff, side: THREE.DoubleSide, transparent: true });
    const hostRing = new THREE.Mesh(hostRingGeo, hostRingMat);
    hostRing.position.copy(hostPos);
    hostRing.lookAt(new THREE.Vector3(0, 0, 0));
    mainGroup.add(hostRing);
    ringsRef.current.push(hostRing);

    // Resize observer
    const resizeObserver = new ResizeObserver(() => {
      if (!mountRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = 560;
      rendererRef.current.setSize(w, h);
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
    });
    resizeObserver.observe(mountRef.current);

    // Interaction handlers
    const onMouseDown = (e: MouseEvent) => {
      isDraggingRef.current = true;
      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
      lastInteractTimeRef.current = Date.now();
    };

    const onMouseMove = (e: MouseEvent) => {
      if (isDraggingRef.current && mainGroup) {
        const deltaX = e.clientX - previousMousePositionRef.current.x;
        const deltaY = e.clientY - previousMousePositionRef.current.y;
        
        mainGroup.rotation.y += deltaX * 0.005;
        mainGroup.rotation.x += deltaY * 0.005;
        mainGroup.rotation.x = Math.max(-1.2, Math.min(1.2, mainGroup.rotation.x));
        
        rotationVelocityRef.current = { x: deltaX * 0.005, y: deltaY * 0.005 };
        previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
        lastInteractTimeRef.current = Date.now();
      }

      // Raycasting for tooltip
      if (mountRef.current && cameraRef.current && dotMeshesRef.current.length > 0) {
        const rect = mountRef.current.getBoundingClientRect();
        const mouse = new THREE.Vector2(
          ((e.clientX - rect.left) / rect.width) * 2 - 1,
          -((e.clientY - rect.top) / rect.height) * 2 + 1
        );

        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, cameraRef.current);
        const intersects = raycaster.intersectObjects(dotMeshesRef.current.map(d => d.mesh));

        if (intersects.length > 0) {
          const intersected = dotMeshesRef.current.find(d => d.mesh === intersects[0].object);
          if (intersected) {
            setTooltip({
              ip: intersected.data.ip,
              location: `${intersected.data.city || 'Unknown'}, ${intersected.data.country_name}`,
              count: intersected.data.count,
              direction: intersected.data.direction,
              x: e.clientX - rect.left + 14,
              y: e.clientY - rect.top - 10
            });
          }
        } else {
          setTooltip(null);
        }
      }
    };

    const onMouseUp = () => {
      isDraggingRef.current = false;
    };

    const onMouseLeave = () => {
      isDraggingRef.current = false;
      setTooltip(null);
    };

    mountRef.current.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    mountRef.current.addEventListener('mouseleave', onMouseLeave);

    // Animation loop
    const animate = () => {
      animFrameRef.current = requestAnimationFrame(animate);

      const now = Date.now();
      const timeSinceInteract = now - lastInteractTimeRef.current;
      
      if (mainGroup) {
        // Auto rotate
        if (autoRotateRef.current && !isDraggingRef.current && timeSinceInteract > 3000) {
          mainGroup.rotation.y += 0.0015;
        }

        // Inertia
        if (!isDraggingRef.current && (Math.abs(rotationVelocityRef.current.x) > 0.0001 || Math.abs(rotationVelocityRef.current.y) > 0.0001)) {
          mainGroup.rotation.y += rotationVelocityRef.current.x;
          mainGroup.rotation.x += rotationVelocityRef.current.y;
          mainGroup.rotation.x = Math.max(-1.2, Math.min(1.2, mainGroup.rotation.x));
          
          rotationVelocityRef.current.x *= 0.95;
          rotationVelocityRef.current.y *= 0.95;
        }

        // Pulse rings
        const pulseScale = 1 + Math.sin(now * 0.004) * 0.25; // 1 to 1.5
        ringsRef.current.forEach((ring, i) => {
          // Staggered phase for markers
          const phase = i === 0 ? now * 0.004 : (now * 0.004 + i * 0.5);
          const s = 1 + (Math.sin(phase) + 1) * 0.25; // 1 to 1.5
          ring.scale.set(s, s, 1);
        });

        // Update particles
        particlesRef.current.forEach(p => {
          p.progress += p.speed;
          if (p.progress > 1) p.progress = 0;
          const pos = p.curve.getPoint(p.progress);
          p.mesh.position.copy(pos);
        });

        // Back-face culling for dots
        if (cameraRef.current) {
          const cameraNorm = cameraRef.current.position.clone().normalize();
          dotMeshesRef.current.forEach(({ mesh }) => {
            const worldPos = new THREE.Vector3();
            mesh.getWorldPosition(worldPos);
            const facing = worldPos.clone().normalize().dot(cameraNorm);
            if (mesh.material instanceof THREE.MeshBasicMaterial) {
               mesh.material.opacity = facing > 0.1 ? 1.0 : 0.08;
               mesh.material.transparent = true;
            }
          });
        }
      }

      renderer.render(scene, camera);
    };
    animate();

    // Cleanup
    return () => {
      cancelAnimationFrame(animFrameRef.current);
      resizeObserver.disconnect();
      mountRef.current?.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      mountRef.current?.removeEventListener('mouseleave', onMouseLeave);
      
      renderer.dispose();
      scene.traverse((obj) => {
        if (obj instanceof THREE.Mesh) {
          obj.geometry.dispose();
          if (Array.isArray(obj.material)) {
            obj.material.forEach(m => m.dispose());
          } else {
            obj.material.dispose();
          }
        }
      });
      if (mountRef.current && renderer.domElement.parentNode === mountRef.current) {
        mountRef.current.removeChild(renderer.domElement);
      }
    };
  }, []);

  // Update points and arcs
  useEffect(() => {
    if (!pointsGroupRef.current || !arcsGroupRef.current || !groupRef.current) return;

    // Clear previous
    while (pointsGroupRef.current.children.length > 0) {
      const obj = pointsGroupRef.current.children[0];
      if (obj instanceof THREE.Mesh) {
        obj.geometry.dispose();
        if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
        else obj.material.dispose();
      }
      pointsGroupRef.current.remove(obj);
    }
    
    while (arcsGroupRef.current.children.length > 0) {
      const obj = arcsGroupRef.current.children[0];
      if (obj instanceof THREE.Mesh || obj instanceof THREE.Line) {
        obj.geometry.dispose();
        if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
        else obj.material.dispose();
      }
      arcsGroupRef.current.remove(obj);
    }

    dotMeshesRef.current = [];
    particlesRef.current = [];
    // Keep host ring (first in ringsRef)
    const hostRing = ringsRef.current[0];
    ringsRef.current = [hostRing];

    const hostPos = latLngToVec3(20.59, 78.96, 1.013);

    points.forEach((point, i) => {
      const pos = latLngToVec3(point.latitude, point.longitude, 1.013);
      const color = point.direction === 'source' ? 0x7c6fe0 : 0x3dba8c;
      const size = Math.max(0.008, Math.min(0.022, Math.log(point.count) * 0.003));
      
      // Dot
      const dotGeo = new THREE.SphereGeometry(size, 8, 8);
      const dotMat = new THREE.MeshBasicMaterial({ color, transparent: true });
      const dot = new THREE.Mesh(dotGeo, dotMat);
      dot.position.copy(pos);
      pointsGroupRef.current!.add(dot);
      dotMeshesRef.current.push({ mesh: dot, data: point });

      // Ring
      const ringGeo = new THREE.RingGeometry(size * 1.5, size * 2.2, 16);
      const ringMat = new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide, transparent: true, opacity: 0.6 });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.copy(pos);
      ring.lookAt(new THREE.Vector3(0, 0, 0));
      pointsGroupRef.current!.add(ring);
      ringsRef.current.push(ring);

      // Arc
      const mid = pos.clone().add(hostPos).multiplyScalar(0.5);
      const lift = Math.max(0.3, Math.min(0.8, pos.distanceTo(hostPos) * 0.5));
      mid.normalize().multiplyScalar(1.02 + lift);
      const curve = new THREE.QuadraticBezierCurve3(pos, mid, hostPos);
      const curvePoints = curve.getPoints(60);
      const arcGeo = new THREE.BufferGeometry().setFromPoints(curvePoints);
      const arcMat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.45 });
      const arc = new THREE.Line(arcGeo, arcMat);
      arcsGroupRef.current!.add(arc);

      // Particle
      const partGeo = new THREE.SphereGeometry(0.006, 6, 6);
      const partMat = new THREE.MeshBasicMaterial({ color });
      const particle = new THREE.Mesh(partGeo, partMat);
      arcsGroupRef.current!.add(particle);
      particlesRef.current.push({
        mesh: particle,
        curve,
        progress: Math.random(),
        speed: 0.003 + Math.random() * 0.003
      });
    });
  }, [points]);

  const uniqueCountries = useMemo(() => new Set(points.map(p => p.country_code)).size, [points]);

  return (
    <div ref={containerRef} className="relative w-full overflow-hidden rounded-2xl glass-panel" style={{ height: '560px' }}>
      <div ref={mountRef} className="h-full w-full cursor-grab active:cursor-grabbing" />
      
      {/* Top-left HUD */}
      <div className="absolute left-6 top-6 flex flex-col gap-2 pointer-events-none">
        <div className="flex items-center gap-2 px-3 py-1.5 glass-panel rounded-full">
          <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
          <span className="text-[11px] font-medium tracking-wider text-foreground uppercase">Live intelligence</span>
        </div>
        <div className="px-3 py-1.5 glass-panel rounded-full">
          <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
            {uniqueCountries} Countries reached
          </span>
        </div>
      </div>

      {/* Controls HUD */}
      <div className="absolute bottom-6 right-6 flex flex-col gap-2">
        <button 
          onClick={() => setAutoRotate(!autoRotate)}
          className={`px-3 py-1.5 rounded-lg text-[10px] font-medium uppercase tracking-wider transition-all border ${autoRotate ? 'bg-primary/20 border-primary/40 text-primary' : 'bg-card/40 border-border/40 text-muted-foreground'}`}
        >
          Auto-rotate: {autoRotate ? 'On' : 'Off'}
        </button>
        <button 
          onClick={() => setShowArcs(!showArcs)}
          className={`px-3 py-1.5 rounded-lg text-[10px] font-medium uppercase tracking-wider transition-all border ${showArcs ? 'bg-primary/20 border-primary/40 text-primary' : 'bg-card/40 border-border/40 text-muted-foreground'}`}
        >
          Arcs: {showArcs ? 'On' : 'Off'}
        </button>
        <button 
          onClick={() => setShowAtmosphere(!showAtmosphere)}
          className={`px-3 py-1.5 rounded-lg text-[10px] font-medium uppercase tracking-wider transition-all border ${showAtmosphere ? 'bg-primary/20 border-primary/40 text-primary' : 'bg-card/40 border-border/40 text-muted-foreground'}`}
        >
          Atmosphere: {showAtmosphere ? 'On' : 'Off'}
        </button>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div 
          style={{
            position: 'absolute',
            left: tooltip.x,
            top: tooltip.y,
            background: 'rgba(6,12,28,0.92)',
            border: '0.5px solid rgba(255,255,255,0.1)',
            borderRadius: '10px',
            padding: '10px 14px',
            fontSize: '12px',
            color: '#c8d8f0',
            pointerEvents: 'none',
            minWidth: '155px',
            zIndex: 10,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontWeight: 600 }}>{tooltip.ip}</span>
            <span style={{ 
              color: tooltip.direction === 'source' ? '#7c6fe0' : '#3dba8c',
              fontSize: '10px',
              textTransform: 'uppercase',
              fontWeight: 700
            }}>
              {tooltip.direction}
            </span>
          </div>
          <div style={{ opacity: 0.7, fontSize: '11px' }}>{tooltip.location}</div>
          <div style={{ marginTop: '4px', fontSize: '11px' }}>
            <span style={{ opacity: 0.5 }}>Traffic: </span>
            <span>{tooltip.count} packets</span>
          </div>
        </div>
      )}

      {/* Empty State */}
      {points.length === 0 && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px', pointerEvents: 'none' }}>
          <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.3)' }}>No geo-resolved traffic yet</span>
          <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.15)' }}>Start a capture session to see origins</span>
        </div>
      )}
    </div>
  );
}
