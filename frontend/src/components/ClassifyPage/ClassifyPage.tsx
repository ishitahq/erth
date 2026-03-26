import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  detectImage,
  CLASS_COLORS,
  GRADE_COLORS,
} from '../../utils/mockInference';
import type { DetectionResult } from '../../utils/mockInference';

type Stage = 'upload' | 'scanning' | 'results' | 'error';
type InputMode = 'upload' | 'webcam';

interface CameraDevice {
  deviceId: string;
  label: string;
}

const ClassifyPage = () => {
  const [stage, setStage] = useState<Stage>('upload');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string>('');
  const [detectResult, setDetectResult] = useState<DetectionResult | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [inputMode, setInputMode] = useState<InputMode>('upload');
  const [webcamActive, setWebcamActive] = useState(false);
  const [cameras, setCameras] = useState<CameraDevice[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<string>('');
  const [inferenceTime, setInferenceTime] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const navigate = useNavigate();

  // Enumerate cameras
  useEffect(() => {
    if (inputMode !== 'webcam') return;
    const listCameras = async () => {
      try {
        const tempStream = await navigator.mediaDevices.getUserMedia({ video: true });
        const devices = await navigator.mediaDevices.enumerateDevices();
        tempStream.getTracks().forEach((t) => t.stop());
        const videoDevices = devices
          .filter((d) => d.kind === 'videoinput')
          .map((d, i) => ({ deviceId: d.deviceId, label: d.label || `Camera ${i + 1}` }));
        setCameras(videoDevices);
        if (videoDevices.length > 0 && !selectedCamera) {
          setSelectedCamera(videoDevices[0].deviceId);
        }
      } catch { /* permission denied */ }
    };
    listCameras();
  }, [inputMode, selectedCamera]);

  useEffect(() => {
    return () => {
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const stopWebcam = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setWebcamActive(false);
  }, []);

  const startWebcam = useCallback(async () => {
    try {
      const constraints: MediaStreamConstraints = {
        video: selectedCamera
          ? { deviceId: { exact: selectedCamera }, width: { ideal: 1280 }, height: { ideal: 720 } }
          : { width: { ideal: 1280 }, height: { ideal: 720 } },
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => videoRef.current?.play();
      }
      setWebcamActive(true);
    } catch {
      alert('Could not access webcam. Check browser permissions.');
    }
  }, [selectedCamera]);

  const captureWebcam = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    if (!vw || !vh) { alert('Camera not ready yet.'); return; }
    canvas.width = vw;
    canvas.height = vh;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, vw, vh);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' });
      setImageFile(file);
      setImageUrl(URL.createObjectURL(blob));
      stopWebcam();
      setStage('upload');
      setResult(null);
    }, 'image/jpeg', 0.92);
  }, [stopWebcam]);

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) return;
    setImageFile(file);
    setImageUrl(URL.createObjectURL(file));
    setStage('upload');
    setResult(null);
    setErrorMsg('');
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleAnalyze = async () => {
    if (!imageFile) return;
    setStage('scanning');
    setErrorMsg('');
    const t0 = performance.now();
    try {
      const res = await detectImage(imageFile);
      setInferenceTime(Math.round(performance.now() - t0));
      setDetectResult(res);
      setStage('results');
    } catch (err: unknown) {
      setInferenceTime(0);
      setErrorMsg(err instanceof Error ? err.message : 'Could not connect to the backend. Is the server running on port 8000?');
      setStage('error');
    }
  };

  const handleReset = () => {
    setStage('upload');
    setImageFile(null);
    setImageUrl('');
    setDetectResult(null);
    setErrorMsg('');
  };

  const switchMode = (mode: InputMode) => {
    handleReset();
    if (mode === 'upload') stopWebcam();
    setInputMode(mode);
  };

  return (
    <div className="min-h-screen bg-site-black text-site-text-light">
      {/* Top bar */}
      <div className="w-full bg-site-dark text-site-text-light text-center py-2 text-xs md:text-sm tracking-widest uppercase font-medium">
        🏭 Conveyor Belt Plastic Detection Engine
      </div>

      {/* Toggle navbar */}
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="fixed top-10 left-0 right-0 z-50 flex justify-center pointer-events-none"
      >
        <div className="bg-site-dark/90 backdrop-blur-xl rounded-full p-1 inline-flex items-center border border-gray-700/50 shadow-2xl pointer-events-auto">
          <button
            onClick={() => navigate('/')}
            className="relative px-6 py-2.5 rounded-full text-xs font-bold tracking-widest uppercase transition-all duration-300 text-site-text-muted hover:text-white"
          >
            Home
          </button>
          <button className="relative px-6 py-2.5 rounded-full text-xs font-bold tracking-widest uppercase transition-all duration-300 text-black">
            <motion.div
              layoutId="nav-pill"
              className="absolute inset-0 bg-[#7ed957] rounded-full"
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
            <span className="relative z-10">Classify</span>
          </button>
        </div>
      </motion.nav>

      {/* Hero */}
      <section className="pt-28 pb-10 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="section-container"
        >
          <p className="text-[#7ed957] text-xs md:text-sm uppercase tracking-[0.3em] mb-4 font-bold">Core Feature</p>
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-black tracking-tight mb-4 leading-tight">
            Detect Your{' '}
            <span className="bg-gradient-to-r from-[#7ed957] to-[#5cb83f] bg-clip-text text-transparent">Plastics</span>
          </h1>
          <p className="text-sm md:text-base text-site-text-muted max-w-xl mx-auto leading-relaxed">
            Upload a conveyor belt image. Our AI detects every plastic item, classifies its type,
            assigns a recyclability grade, and estimates volume per object.
          </p>
        </motion.div>
      </section>

      {/* Main content */}
      <section className="pb-20">
        <div className="section-container">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            {/* LEFT — Input */}
            <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, delay: 0.2 }}>
              {/* Upload / Webcam toggle */}
              <div className="flex justify-center mb-6">
                <div className="bg-white/[0.05] rounded-full p-1 flex border border-gray-700/50">
                  <button
                    onClick={() => switchMode('upload')}
                    className={`px-5 py-2 rounded-full text-xs font-bold tracking-wider uppercase transition-all duration-300 ${inputMode === 'upload' ? 'bg-[#7ed957] text-black' : 'text-site-text-muted hover:text-white'}`}
                  >
                    📁 Upload
                  </button>
                  <button
                    onClick={() => switchMode('webcam')}
                    className={`px-5 py-2 rounded-full text-xs font-bold tracking-wider uppercase transition-all duration-300 ${inputMode === 'webcam' ? 'bg-[#7ed957] text-black' : 'text-site-text-muted hover:text-white'}`}
                  >
                    📷 Webcam
                  </button>
                </div>
              </div>

              {/* Upload zone */}
              {inputMode === 'upload' && !imageUrl && (
                <div
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`relative cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-300
                    flex flex-col items-center justify-center min-h-[420px]
                    ${isDragging ? 'border-[#7ed957] bg-[#7ed957]/10 scale-[1.02]' : 'border-gray-600 bg-white/[0.03] hover:border-gray-400 hover:bg-white/[0.05]'}`}
                >
                  <motion.div animate={{ y: [0, -8, 0] }} transition={{ repeat: Infinity, duration: 2.5, ease: 'easeInOut' }} className="mb-6">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke={isDragging ? '#7ed957' : '#666'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </motion.div>
                  <p className="text-lg font-bold text-site-text-light mb-1">{isDragging ? 'Drop it here!' : 'Drag & drop your image'}</p>
                  <p className="text-sm text-site-text-muted">or <span className="text-[#7ed957] underline">browse files</span></p>
                  <p className="text-xs text-site-text-muted/60 mt-3">JPG, PNG, BMP — up to 10 MB</p>
                  <input ref={fileInputRef} type="file" accept="image/*" onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} className="hidden" />
                </div>
              )}

              {/* Webcam zone */}
              {inputMode === 'webcam' && !imageUrl && (
                <div className="rounded-2xl overflow-hidden bg-site-dark border border-gray-700/50">
                  <div className="relative min-h-[420px] flex items-center justify-center bg-black/50">
                    {!webcamActive ? (
                      <div className="text-center">
                        <motion.div animate={{ scale: [1, 1.1, 1] }} transition={{ repeat: Infinity, duration: 2 }} className="mx-auto mb-4 w-20 h-20 rounded-full bg-white/10 flex items-center justify-center">
                          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#7ed957" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                            <circle cx="12" cy="13" r="4" />
                          </svg>
                        </motion.div>
                        {cameras.length > 1 && (
                          <div className="mb-4">
                            <p className="text-xs text-site-text-muted mb-2 font-medium">Select Camera</p>
                            <select value={selectedCamera} onChange={(e) => setSelectedCamera(e.target.value)}
                              className="bg-white/10 text-white text-xs rounded-lg px-3 py-2 border border-gray-600 outline-none focus:border-[#7ed957] transition-colors w-64">
                              {cameras.map((cam) => (<option key={cam.deviceId} value={cam.deviceId} className="bg-gray-900">{cam.label}</option>))}
                            </select>
                          </div>
                        )}
                        <button onClick={startWebcam} className="px-6 py-3 bg-[#7ed957] text-black rounded-xl font-bold text-sm hover:bg-[#5cb83f] transition-all hover:scale-[1.02]">Start Camera</button>
                        <p className="text-xs text-site-text-muted/60 mt-3">{cameras.length > 1 ? 'Select your camera above, then start' : 'Allow camera access when prompted'}</p>
                      </div>
                    ) : (
                      <>
                        <video ref={videoRef} autoPlay playsInline muted className="w-full h-auto max-h-[420px] object-contain" />
                        <div className="absolute inset-8 pointer-events-none">
                          <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-[#7ed957] rounded-tl-md" />
                          <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-[#7ed957] rounded-tr-md" />
                          <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-[#7ed957] rounded-bl-md" />
                          <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-[#7ed957] rounded-br-md" />
                        </div>
                      </>
                    )}
                    <canvas ref={canvasRef} className="hidden" />
                  </div>
                  {webcamActive && (
                    <div className="p-4 flex gap-3 border-t border-gray-700/50">
                      <button onClick={captureWebcam} className="flex-1 py-3 rounded-xl font-bold text-sm bg-[#7ed957] text-black hover:bg-[#5cb83f] transition-all hover:scale-[1.02] active:scale-[0.98]">📸 Capture Photo</button>
                      <button onClick={stopWebcam} className="px-4 py-3 rounded-xl font-bold text-sm bg-white/10 text-white hover:bg-white/20 transition-all">✕</button>
                    </div>
                  )}
                </div>
              )}

              {/* Image preview with scanning animation */}
              {imageUrl && (
                <div className="relative rounded-2xl overflow-hidden bg-site-dark border border-gray-700/50">
                  <div className="relative">
                    <img src={imageUrl} alt="Plastic to classify" className="w-full h-auto max-h-[520px] object-contain bg-black/50" />
                    <AnimatePresence>
                      {stage === 'scanning' && (
                        <>
                          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-[#7ed957]/5" />
                          <motion.div initial={{ top: 0 }} animate={{ top: '100%' }} transition={{ duration: 1.8, repeat: Infinity, ease: 'linear' }}
                            className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#7ed957] to-transparent shadow-[0_0_20px_#7ed957]" />
                          <motion.div initial={{ opacity: 0 }} animate={{ opacity: [0.3, 0.6, 0.3] }} transition={{ duration: 1.5, repeat: Infinity }}
                            className="absolute inset-0 flex items-center justify-center">
                            <div className="bg-black/70 backdrop-blur-sm rounded-xl px-6 py-3">
                              <p className="text-[#7ed957] text-sm font-bold tracking-widest uppercase animate-pulse">🔍 Analyzing...</p>
                            </div>
                          </motion.div>
                        </>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Action bar */}
                  <div className="p-4 flex gap-3 border-t border-gray-700/50">
                    {stage === 'upload' && (
                      <>
                        <button onClick={handleAnalyze}
                          className="flex-1 py-3 rounded-xl font-bold text-sm transition-all hover:scale-[1.02] active:scale-[0.98] bg-[#7ed957] text-black hover:bg-[#5cb83f]">
                          🏭 Detect Objects
                        </button>
                        <button onClick={handleReset} className="px-4 py-3 rounded-xl font-bold text-sm bg-white/10 text-white hover:bg-white/20 transition-all">✕</button>
                      </>
                    )}
                    {stage === 'scanning' && (
                      <div className="flex-1 py-3 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-[#7ed957] animate-pulse" />
                          <span className="text-sm text-site-text-muted font-medium">Detecting objects...</span>
                        </div>
                      </div>
                    )}
                    {(stage === 'results' || stage === 'error') && (
                      <>
                        <button onClick={handleReset} className="flex-1 py-3 rounded-xl font-bold text-sm bg-[#7ed957] text-black hover:bg-[#5cb83f] transition-all hover:scale-[1.02]">↻ Classify Another</button>
                        {inferenceTime > 0 && (
                          <div className="px-4 py-3 rounded-xl bg-white/5 text-xs text-site-text-muted font-medium flex items-center">{inferenceTime}ms</div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}
            </motion.div>

            {/* RIGHT — Results panel */}
            <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, delay: 0.4 }} className="space-y-4">

              {/* Status card */}
              <div className="bg-white/[0.03] border border-gray-700/50 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-3 h-3 rounded-full ${stage === 'results' ? 'bg-[#7ed957]' : stage === 'scanning' ? 'bg-yellow-400 animate-pulse' : stage === 'error' ? 'bg-red-500' : 'bg-gray-500'}`} />
                  <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted">
                    {stage === 'upload' ? 'Awaiting Image' : stage === 'scanning' ? 'Detecting Objects' : stage === 'error' ? 'Error' : 'Detection Complete'}
                  </p>
                </div>
                {stage === 'upload' && !imageUrl && (
                  <p className="text-sm text-site-text-muted leading-relaxed">Upload a conveyor belt image or capture one from your webcam. AI will detect every plastic item, classify its type, grade it, and estimate its volume.</p>
                )}
                {stage === 'upload' && imageUrl && (
                  <p className="text-sm text-site-text-muted leading-relaxed">Image loaded. Click <span className="text-[#7ed957] font-semibold">Detect Objects</span> to run the full detection pipeline.</p>
                )}
                {stage === 'scanning' && (
                  <div className="space-y-3">
                    {[
                      'Detecting plastic objects (OpenCV / YOLO)...',
                      'Stage 1: Classifying each detected item...',
                      'Stage 2: CLIP grade per object...',
                      'Stage 3: Volume estimation per object...',
                    ].map((step, i) => (
                      <motion.div key={step} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.5 }} className="flex items-center gap-2">
                        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }} className="w-3 h-3 border-2 border-[#7ed957] border-t-transparent rounded-full" />
                        <span className="text-xs text-site-text-muted">{step}</span>
                      </motion.div>
                    ))}
                  </div>
                )}
                {stage === 'error' && (
                  <p className="text-sm text-red-400 leading-relaxed">{errorMsg}</p>
                )}
              </div>

              {/* ── CONVEYOR MODE RESULTS ── */}
              <AnimatePresence>
                {stage === 'results' && detectResult && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="space-y-4">

                    {/* Annotated image */}
                    {detectResult.annotated_image_b64 && (
                      <div className="bg-white/[0.03] border border-gray-700/50 rounded-2xl overflow-hidden">
                        <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted px-5 pt-5 pb-3">Annotated Output</p>
                        <img
                          src={`data:image/jpeg;base64,${detectResult.annotated_image_b64}`}
                          alt="Annotated detections"
                          className="w-full h-auto object-contain max-h-[420px] bg-black/50"
                        />
                      </div>
                    )}

                    {/* Summary card */}
                    <div className="bg-white/[0.03] border border-gray-700/50 rounded-2xl p-5">
                      <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted mb-4">
                        Detection Summary — {detectResult.summary.total_objects} Object{detectResult.summary.total_objects !== 1 ? 's' : ''} Found
                      </p>
                      <div className="grid grid-cols-2 gap-3 mb-4">
                        {/* Type breakdown */}
                        <div className="bg-white/[0.05] rounded-xl p-3">
                          <p className="text-[10px] text-site-text-muted/60 uppercase tracking-wider font-bold mb-2">By Type</p>
                          <div className="space-y-1">
                            {Object.entries(detectResult.summary.type_counts).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
                              <div key={type} className="flex items-center justify-between">
                                <div className="flex items-center gap-1.5">
                                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: CLASS_COLORS[type] || '#6b7280' }} />
                                  <span className="text-xs font-bold text-white">{type}</span>
                                </div>
                                <span className="text-xs font-mono text-site-text-muted">×{count}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                        {/* Grade breakdown */}
                        <div className="bg-white/[0.05] rounded-xl p-3">
                          <p className="text-[10px] text-site-text-muted/60 uppercase tracking-wider font-bold mb-2">By Grade</p>
                          <div className="space-y-1">
                            {Object.entries(detectResult.summary.grade_counts).sort().map(([grade, count]) => (
                              <div key={grade} className="flex items-center justify-between">
                                <div className="flex items-center gap-1.5">
                                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: GRADE_COLORS[grade] || '#6b7280' }} />
                                  <span className="text-xs font-bold text-white">Grade {grade}</span>
                                </div>
                                <span className="text-xs font-mono text-site-text-muted">×{count}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                      {detectResult.summary.total_volume_cm3 != null && (
                        <div className="flex items-center justify-between p-3 bg-white/[0.05] rounded-xl">
                          <span className="text-xs font-bold text-site-text-muted uppercase tracking-wider">Total Volume</span>
                          <span className="text-xl font-black text-[#7ed957]">{detectResult.summary.total_volume_cm3} cm³</span>
                        </div>
                      )}
                      <div className="mt-2 text-right">
                        <span className="text-[10px] text-site-text-muted/50 uppercase tracking-wider">
                          Detector: {detectResult.detection_method}
                        </span>
                      </div>
                    </div>

                    {/* Per-object cards */}
                    <div className="space-y-3">
                      <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted">Per-Object Analysis</p>
                      {detectResult.objects.map((obj) => (
                        <motion.div
                          key={obj.object_id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: obj.object_id * 0.06 }}
                          className="bg-white/[0.03] border border-gray-700/50 rounded-xl p-4"
                        >
                          <div className="flex items-start gap-3">
                            {/* ID badge */}
                            <div
                              className="w-9 h-9 rounded-lg flex items-center justify-center text-sm font-black text-white shrink-0"
                              style={{ backgroundColor: CLASS_COLORS[obj.plastic_type] || '#6b7280' }}
                            >
                              #{obj.object_id}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm font-black text-white">{obj.plastic_type}</span>
                                <span className="text-xs text-site-text-muted">
                                  {(obj.type_confidence * 100).toFixed(0)}% conf
                                </span>
                                {obj.grade && (
                                  <span
                                    className="text-xs font-bold px-2 py-0.5 rounded-full text-black"
                                    style={{ backgroundColor: GRADE_COLORS[obj.grade] || '#6b7280' }}
                                  >
                                    Grade {obj.grade}
                                  </span>
                                )}
                                {obj.volume_cm3 != null && (
                                  <span className="text-xs text-[#7ed957] font-mono">{obj.volume_cm3} cm³</span>
                                )}
                              </div>
                              {obj.action && (
                                <p className="text-xs text-site-text-muted/70 mt-1">{obj.action}</p>
                              )}
                              {/* Mini score bars */}
                              {obj.all_class_scores && (
                                <div className="mt-2 grid grid-cols-3 gap-1">
                                  {Object.entries(obj.all_class_scores)
                                    .sort((a, b) => b[1] - a[1])
                                    .slice(0, 3)
                                    .map(([cls, score]) => (
                                      <div key={cls} className="text-center">
                                        <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                                          <div
                                            className="h-full rounded-full"
                                            style={{
                                              width: `${score * 100}%`,
                                              backgroundColor: CLASS_COLORS[cls] || '#666',
                                            }}
                                          />
                                        </div>
                                        <p className="text-[9px] text-site-text-muted/50 mt-0.5">{cls} {(score * 100).toFixed(0)}%</p>
                                      </div>
                                    ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>

                  </motion.div>
                )}
              </AnimatePresence>



              {/* Pipeline info card (visible when no results) */}
              {stage !== 'results' && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.6 }}
                  className="bg-white/[0.03] border border-gray-700/50 rounded-2xl p-5">
                  <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted mb-3">Detection Pipeline</p>
                  <div className="space-y-3">
                    {[
                      { num: '🎯', title: 'Object Detection', desc: 'OpenCV / YOLO — locates every plastic item with bounding boxes', color: '#7ed957' },
                      { num: '1', title: 'Type Classification', desc: 'EfficientNet-B3 — identifies HDPE, LDPE, PET, PP, PS, or Other per item', color: '#7ed957' },
                      { num: '2', title: 'Recyclability Grade', desc: 'CLIP ViT-B/32 zero-shot — Grade A / B / C per item', color: '#f59e0b' },
                      { num: '3', title: 'Volumetric Estimation', desc: 'Depth Anything V2 — estimates volume in cm³ per item', color: '#a78bfa' },
                    ].map((s) => (
                      <div key={s.num} className="flex items-start gap-3">
                        <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-black text-white shrink-0" style={{ backgroundColor: s.color }}>
                          {s.num}
                        </div>
                        <div>
                          <p className="text-sm font-bold text-white">{s.title}</p>
                          <p className="text-xs text-site-text-muted/70">{s.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default ClassifyPage;
