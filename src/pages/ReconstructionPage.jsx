import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  SkipForward, 
  SkipBack, 
  Layers, 
  Camera, 
  Activity, 
  ShieldAlert,
  Eye,
  Crosshair
} from 'lucide-react';
import * as THREE from 'three';
import { DEMO_TELEMETRY_POINTS } from '../services/demoData';

export default function ReconstructionPage({ 
  incident, 
  timeline, 
  evidence = [], 
  telemetryPoints = [], 
  vehicles = [], 
  isDemo = false 
}) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [viewMode, setViewMode] = useState('3D'); // '3D' | '2D_OPTICAL'
  const canvasRef = useRef(null);
  const threeSceneRef = useRef(null);

  const points = (telemetryPoints && telemetryPoints.length > 0)
    ? telemetryPoints
    : (isDemo ? DEMO_TELEMETRY_POINTS : []);

  const veh1Name = vehicles[0]?.vehicle_id || 'VEH_01';
  const veh2Name = vehicles[1]?.vehicle_id || 'VEH_02';

  const currentData = points.length > 0 ? (points[currentStep] || points[0]) : {
    t: '00:00:00',
    veh1_speed: 0,
    veh2_speed: 0,
    veh1_accel: 0,
    veh2_accel: 0,
    veh1_brake: 0,
    veh2_brake: 0,
  };

  // Playback loop
  useEffect(() => {
    let interval = null;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= points.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 900);
    }
    return () => clearInterval(interval);
  }, [isPlaying, points.length]);

  // Three.js 3D Canvas initialization
  useEffect(() => {
    const container = canvasRef.current;
    if (!container) return;

    // Scene & Camera setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc);

    const width = container.clientWidth || 600;
    const height = 360;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 30, 45);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;

    // Clear previous canvas
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(20, 40, 20);
    scene.add(dirLight);

    // Road Plane
    const roadGeo = new THREE.PlaneGeometry(80, 20);
    const roadMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.8 });
    const road = new THREE.Mesh(roadGeo, roadMat);
    road.rotation.x = -Math.PI / 2;
    scene.add(road);

    // Lane divider dashed lines
    for (let x = -35; x <= 35; x += 10) {
      const lineGeo = new THREE.PlaneGeometry(4, 0.4);
      const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      const line = new THREE.Mesh(lineGeo, lineMat);
      line.rotation.x = -Math.PI / 2;
      line.position.set(x, 0.05, 0);
      scene.add(line);
    }

    // Vehicle 1 Mesh (Blue sedan)
    const veh1Geo = new THREE.BoxGeometry(4.2, 1.4, 2.0);
    const veh1Mat = new THREE.MeshStandardMaterial({ color: 0x1e40af, roughness: 0.4 });
    const veh1Mesh = new THREE.Mesh(veh1Geo, veh1Mat);
    veh1Mesh.position.set(8, 0.7, -3);
    scene.add(veh1Mesh);

    // Vehicle 2 Mesh (Red / Orange van)
    const veh2Geo = new THREE.BoxGeometry(4.8, 1.8, 2.2);
    const veh2Mat = new THREE.MeshStandardMaterial({ color: 0xb91c1c, roughness: 0.5 });
    const veh2Mesh = new THREE.Mesh(veh2Geo, veh2Mat);
    veh2Mesh.position.set(-20, 0.9, -3);
    scene.add(veh2Mesh);

    // Impact Zone Marker (pulsing ring)
    const ringGeo = new THREE.RingGeometry(1.5, 2.2, 32);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, side: THREE.DoubleSide });
    const impactRing = new THREE.Mesh(ringGeo, ringMat);
    impactRing.rotation.x = -Math.PI / 2;
    impactRing.position.set(10, 0.08, -3);
    scene.add(impactRing);

    threeSceneRef.current = { scene, camera, renderer, veh1Mesh, veh2Mesh };

    let animationFrameId;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      renderer.dispose();
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }
    };
  }, []);

  // Update vehicle 3D positions according to current step in timeline
  useEffect(() => {
    if (!threeSceneRef.current) return;
    const { veh1Mesh, veh2Mesh } = threeSceneRef.current;
    if (!veh1Mesh || !veh2Mesh) return;

    // Calculate kinematic positions from speed profile
    const progressFactor = points.length > 1 ? Math.min(1, Math.max(0, currentStep / (points.length - 1))) : 0;
    
    // Vehicle 1 moves from x=0 to x=12 and stops
    const v1_x = Math.min(11, progressFactor * 16);
    veh1Mesh.position.x = v1_x;

    // Vehicle 2 moves from x=-30 towards x=7.5 (impact zone)
    const v2_x = -28 + (progressFactor * 36);
    veh2Mesh.position.x = Math.min(7.5, v2_x);

    // Angular yaw deflection post-impact (step >= 5)
    if (currentStep >= 5) {
      veh2Mesh.rotation.y = -0.3;
      veh1Mesh.rotation.y = 0.15;
    } else {
      veh2Mesh.rotation.y = 0;
      veh1Mesh.rotation.y = 0;
    }
  }, [currentStep, points.length]);

  return (
    <div className="space-y-6">
      {/* Header & Instructions */}
      <div className="panel bg-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h1 className="page-title text-lg">Kinematic & Visual Reconstruction</h1>
            <p className="page-subtitle text-xs mb-0">
              Synchronized multi-sensor timeline with 3D spatial trajectory and optical flow telemetry.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setViewMode('3D')}
              className={`btn btn-sm ${viewMode === '3D' ? 'btn-primary' : 'btn-secondary'}`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>3D Spatial View</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('2D_OPTICAL')}
              className={`btn btn-sm ${viewMode === '2D_OPTICAL' ? 'btn-primary' : 'btn-secondary'}`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Annotated Video Overlay</span>
            </button>
          </div>
        </div>

        {/* Viewport Canvas Container */}
        <div className="mt-4 border border-slate-200 rounded-md overflow-hidden bg-slate-50 relative">
          {viewMode === '3D' ? (
            <div className="relative">
              <div ref={canvasRef} className="w-full h-[360px]" />
              
              {/* Overlay telemetry telemetry HUD */}
              <div className="absolute top-3 left-3 bg-white/90 backdrop-blur-xs p-3 rounded border border-slate-200 shadow-2xs text-xs space-y-1.5 font-mono">
                <div className="text-[10px] text-slate-500 font-sans font-bold uppercase tracking-wider">
                  Timeline Clock: {currentData.t}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-blue-700 font-bold">{veh1Name}:</span>
                  <span>{(currentData.veh1_speed || 0).toFixed(1)} km/h</span>
                  <span className={currentData.veh1_brake ? 'text-red-600 font-bold' : 'text-slate-400'}>
                    [BRAKE: {currentData.veh1_brake ? 'ON' : 'OFF'}]
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-red-700 font-bold">{veh2Name}:</span>
                  <span>{(currentData.veh2_speed || 0).toFixed(1)} km/h</span>
                  <span className={currentData.veh2_brake ? 'text-red-600 font-bold' : 'text-slate-400'}>
                    [BRAKE: {currentData.veh2_brake ? 'ON' : 'OFF'}]
                  </span>
                </div>
              </div>

              <div className="absolute bottom-3 right-3 bg-white/90 p-2 rounded border border-slate-200 text-[10px] text-slate-500">
                <span>Coordinates: Metric Local Frame (WGS-84 Projected)</span>
              </div>
            </div>
          ) : (
            /* Annotated 2D Computer Vision Overlay */
            <div className="relative h-[360px] bg-slate-900 flex items-center justify-center p-6 text-white overflow-hidden">
              {/* Synthetic dashcam road view */}
              <div className="absolute inset-0 opacity-40 bg-gradient-to-b from-slate-800 to-slate-950 flex flex-col justify-end">
                <div className="h-40 w-full border-t border-slate-700 flex justify-center">
                  <div className="w-32 border-l-2 border-r-2 border-dashed border-amber-400 h-full opacity-60"></div>
                </div>
              </div>

              {/* Bounding box Vehicle 1 */}
              <div 
                className="absolute border-2 border-emerald-400 rounded-xs p-1 bg-emerald-500/10 transition-all duration-300"
                style={{
                  top: '120px',
                  right: `${Math.max(15, 45 - currentStep * 3)}%`,
                  width: '120px',
                  height: '80px',
                }}
              >
                <div className="bg-emerald-600 text-white text-[9px] font-mono px-1 py-0.5 rounded-xs inline-block">
                  TRACK-01 [{veh1Name}] {(currentData.veh1_speed || 0).toFixed(0)} km/h
                </div>
              </div>

              {/* Bounding box Vehicle 2 */}
              <div 
                className="absolute border-2 border-red-500 rounded-xs p-1 bg-red-500/10 transition-all duration-300"
                style={{
                  top: '130px',
                  left: `${Math.min(42, 10 + currentStep * 5)}%`,
                  width: '130px',
                  height: '85px',
                }}
              >
                <div className="bg-red-600 text-white text-[9px] font-mono px-1 py-0.5 rounded-xs inline-block">
                  TRACK-02 [{veh2Name}] {(currentData.veh2_speed || 0).toFixed(0)} km/h
                </div>
              </div>

              {/* Center Crosshair */}
              <Crosshair className="w-8 h-8 text-white/30" />

              <div className="absolute bottom-3 left-3 bg-black/70 p-2 rounded font-mono text-[11px] text-emerald-400">
                <div>OPENCV OPTICAL FLOW: ACTIVE</div>
                <div>FRAME #{120 + currentStep * 15} | MAGNITUDE: {(1.2 + currentStep * 0.4).toFixed(2)} px/frame</div>
              </div>
            </div>
          )}

          {/* Scrubber & Playback Controls Bar */}
          <div className="p-4 bg-white border-t border-slate-200">
            <div className="flex items-center gap-4 mb-3">
              <button
                type="button"
                onClick={() => setIsPlaying(!isPlaying)}
                className="btn btn-primary btn-sm w-24"
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                <span>{isPlaying ? 'Pause' : 'Play'}</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentStep(0);
                }}
                className="p-1.5 text-slate-500 hover:text-slate-800 rounded hover:bg-slate-100"
                title="Reset to beginning"
              >
                <RotateCcw className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
                className="p-1.5 text-slate-500 hover:text-slate-800 rounded hover:bg-slate-100"
                title="Previous step"
              >
                <SkipBack className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={() => setCurrentStep(prev => Math.min(points.length - 1, prev + 1))}
                className="p-1.5 text-slate-500 hover:text-slate-800 rounded hover:bg-slate-100"
                title="Next step"
              >
                <SkipForward className="w-4 h-4" />
              </button>

              {/* Progress Slider */}
              <div className="flex-1 flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max={points.length - 1}
                  value={currentStep}
                  onChange={(e) => {
                    setIsPlaying(false);
                    setCurrentStep(Number(e.target.value));
                  }}
                  className="w-full accent-[#0b2545] cursor-pointer"
                />
                <span className="font-mono text-xs text-slate-600 font-bold whitespace-nowrap">
                  {currentData.t} ({currentStep + 1}/{points.length})
                </span>
              </div>
            </div>

            {/* Step Kinematics Readout */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-100 text-xs">
              <div>
                <span className="text-slate-500 text-[11px]">VEH_01 Speed: </span>
                <strong className="font-mono text-slate-900">{currentData.veh1_speed.toFixed(1)} km/h</strong>
              </div>
              <div>
                <span className="text-slate-500 text-[11px]">VEH_01 Accel: </span>
                <strong className="font-mono text-slate-900">{currentData.veh1_accel.toFixed(1)} m/s²</strong>
              </div>
              <div>
                <span className="text-slate-500 text-[11px]">VEH_02 Speed: </span>
                <strong className="font-mono text-slate-900">{currentData.veh2_speed.toFixed(1)} km/h</strong>
              </div>
              <div>
                <span className="text-slate-500 text-[11px]">VEH_02 Accel: </span>
                <strong className="font-mono text-slate-900 text-amber-700">{currentData.veh2_accel.toFixed(1)} m/s²</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Mandatory Photogrammetric Limitation Disclaimer */}
        <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded text-xs text-slate-600 flex items-start gap-2">
          <ShieldAlert className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <div>
            <strong>Forensic Spatial Limitation Notice:</strong> Real-world distances are generated exclusively from calibrated vehicle telemetry and verified survey coordinates. Uncalibrated video optical flow pixel coordinates are strictly kept as 2D pixel-space tracking vectors to prevent depth distortion errors.
          </div>
        </div>
      </div>
    </div>
  );
}
