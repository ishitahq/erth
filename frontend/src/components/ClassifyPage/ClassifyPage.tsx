import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  classifyImage,
  CLASS_COLORS,
  GRADE_COLORS,
  GRADE_LABELS,
  RECYCLING_TIPS,
} from '../../utils/mockInference';
import type { ClassificationResult } from '../../utils/mockInference';

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
  const [result, setResult] = useState<ClassificationResult | null>(null);
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
      const res = await classifyImage(imageFile);
      setInferenceTime(Math.round(performance.now() - t0));
      setResult(res);
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
    setResult(null);
    setErrorMsg('');
  };

  const switchMode = (mode: InputMode) => {
    handleReset();
    if (mode === 'upload') stopWebcam();
    setInputMode(mode);
  };

  // Sorted class scores
  const sortedScores = result?.all_class_scores
    ? Object.entries(result.all_class_scores).sort((a, b) => b[1] - a[1])
    : [];

  return (
    <div className="min-h-screen bg-site-black text-site-text-light">
      {/* Top bar */}
      <div className="w-full bg-site-dark text-site-text-light text-center py-2 text-xs md:text-sm tracking-widest uppercase font-medium">
        🔬 AI Plastic Waste Classification Engine
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
            Classify Your{' '}
            <span className="bg-gradient-to-r from-[#7ed957] to-[#5cb83f] bg-clip-text text-transparent">Plastic</span>
          </h1>
          <p className="text-sm md:text-base text-site-text-muted max-w-xl mx-auto leading-relaxed">
            Upload an image or use your webcam. Our 3-stage AI pipeline identifies type,
            assigns a recyclability grade, and estimates volume.
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
                        <button onClick={handleAnalyze} className="flex-1 py-3 rounded-xl font-bold text-sm bg-[#7ed957] text-black hover:bg-[#5cb83f] transition-all hover:scale-[1.02] active:scale-[0.98]">🔍 Analyze Image</button>
                        <button onClick={handleReset} className="px-4 py-3 rounded-xl font-bold text-sm bg-white/10 text-white hover:bg-white/20 transition-all">✕</button>
                      </>
                    )}
                    {stage === 'scanning' && (
                      <div className="flex-1 py-3 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-[#7ed957] animate-pulse" />
                          <span className="text-sm text-site-text-muted font-medium">Running 3-stage pipeline...</span>
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
                    {stage === 'upload' ? 'Awaiting Image' : stage === 'scanning' ? 'Running Pipeline' : stage === 'error' ? 'Error' : 'Classification Complete'}
                  </p>
                </div>
                {stage === 'upload' && !imageUrl && (
                  <p className="text-sm text-site-text-muted leading-relaxed">Upload an image or capture one from your webcam. The 3-stage pipeline will classify type, assign a recyclability grade, and estimate volume.</p>
                )}
                {stage === 'upload' && imageUrl && (
                  <p className="text-sm text-site-text-muted leading-relaxed">Image loaded. Click <span className="text-[#7ed957] font-semibold">Analyze Image</span> to run the full pipeline.</p>
                )}
                {stage === 'scanning' && (
                  <div className="space-y-3">
                    {['Stage 1: EfficientNet-B3 type classification...', 'Stage 2: CLIP recyclability grading...', 'Stage 3: Depth Anything V2 volumetric estimation...'].map((step, i) => (
                      <motion.div key={step} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.6 }} className="flex items-center gap-2">
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

              {/* ── STAGE 1: Type Classification ── */}
              <AnimatePresence>
                {stage === 'results' && result && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="space-y-4">

                    {/* Type result card */}
                    <div className="bg-white/[0.03] border border-gray-700/50 rounded-2xl p-5">
                      <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted mb-4">Stage 1 — Plastic Type</p>
                      <div className="flex items-center gap-4 mb-5">
                        <div className="w-14 h-14 rounded-xl flex items-center justify-center text-lg font-black text-white"
                          style={{ backgroundColor: CLASS_COLORS[result.plastic_type] || '#6b7280' }}>
                          {result.plastic_type === 'Unknown' ? '?' : result.plastic_type}
                        </div>
                        <div>
                          <p className="text-2xl font-black text-white">{result.plastic_type}</p>
                          <p className="text-sm text-site-text-muted">
                            {(result.type_confidence * 100).toFixed(1)}% confidence
                          </p>
                        </div>
                      </div>

                      {/* Class scores bar chart */}
                      <div className="space-y-2">
                        {sortedScores.map(([cls, score], i) => (
                          <motion.div key={cls} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-bold text-site-text-muted">{cls}</span>
                              <span className="text-xs font-mono text-site-text-muted">{(score * 100).toFixed(1)}%</span>
                            </div>
                            <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${score * 100}%` }}
                                transition={{ duration: 0.6, delay: 0.2 + i * 0.08, ease: 'easeOut' }}
                                className="h-full rounded-full"
                                style={{ backgroundColor: CLASS_COLORS[cls] || '#6b7280' }}
                              />
                            </div>
                          </motion.div>
                        ))}
                      </div>

                      {/* Recycling tip */}
                      <div className="mt-4 p-3 bg-white/[0.03] rounded-lg border border-gray-700/30">
                        <p className="text-xs text-site-text-muted/80 leading-relaxed">
                          💡 {RECYCLING_TIPS[result.plastic_type] || 'Check local recycling guidelines.'}
                        </p>
                      </div>
                    </div>

                    {/* ── STAGE 2: Recyclability Grade ── */}
                    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.2 }}
                      className="bg-white/[0.03] border border-gray-700/50 rounded-2xl p-5">
                      <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted mb-4">Stage 2 — Recyclability Grade</p>
                      {result.grade ? (
                        <>
                          <div className="flex items-center gap-4 mb-4">
                            <div className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-black text-white"
                              style={{ backgroundColor: GRADE_COLORS[result.grade] || '#6b7280' }}>
                              {result.grade}
                            </div>
                            <div>
                              <p className="text-xl font-black text-white">{GRADE_LABELS[result.grade] || result.grade}</p>
                              <p className="text-sm text-site-text-muted">{(result.grade_confidence! * 100).toFixed(1)}% confidence</p>
                            </div>
                          </div>
                          {/* Grade scores */}
                          {result.grade_scores && (
                            <div className="flex gap-2 mb-4">
                              {(['A', 'B', 'C'] as const).map((g) => {
                                const score = result.grade_scores?.[g];
                                const isActive = g === result.grade;
                                return (
                                  <div key={g} className={`flex-1 rounded-lg p-2.5 text-center border transition-all ${isActive ? 'border-white/30 bg-white/[0.08]' : 'border-transparent bg-white/[0.03]'}`}>
                                    <p className="text-lg font-black" style={{ color: GRADE_COLORS[g] }}>{score != null ? `${(score * 100).toFixed(0)}%` : '—'}</p>
                                    <p className="text-[10px] text-site-text-muted/60 uppercase tracking-wider font-medium mt-0.5">Grade {g}</p>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                          {result.action && (
                            <div className="p-3 bg-white/[0.03] rounded-lg border border-gray-700/30">
                              <p className="text-xs font-bold text-[#7ed957] mb-1">Recommended Action</p>
                              <p className="text-sm text-site-text-muted">{result.action}</p>
                            </div>
                          )}
                        </>
                      ) : (
                        <p className="text-sm text-site-text-muted/60 italic">Unavailable — CLIP model not loaded</p>
                      )}
                    </motion.div>

                    {/* ── STAGE 3: Volumetric Estimation ── */}
                    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.4 }}
                      className="bg-white/[0.03] border border-gray-700/50 rounded-2xl p-5">
                      <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted mb-4">Stage 3 — Volumetric Estimation</p>
                      {result.volume_cm3 != null ? (
                        <div className="grid grid-cols-3 gap-3">
                          <div className="bg-white/[0.05] rounded-xl p-4 text-center">
                            <p className="text-2xl font-black text-[#7ed957]">{result.volume_cm3}</p>
                            <p className="text-[10px] text-site-text-muted/60 uppercase tracking-wider font-medium mt-1">Volume (cm³)</p>
                          </div>
                          <div className="bg-white/[0.05] rounded-xl p-4 text-center">
                            <p className="text-2xl font-black text-white">{result.dimensions?.width_cm ?? '—'}</p>
                            <p className="text-[10px] text-site-text-muted/60 uppercase tracking-wider font-medium mt-1">Width (cm)</p>
                          </div>
                          <div className="bg-white/[0.05] rounded-xl p-4 text-center">
                            <p className="text-2xl font-black text-white">{result.dimensions?.height_cm ?? '—'}</p>
                            <p className="text-[10px] text-site-text-muted/60 uppercase tracking-wider font-medium mt-1">Height (cm)</p>
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm text-site-text-muted/60 italic">Unavailable — Depth model not loaded</p>
                      )}
                    </motion.div>

                    {/* Meta bar */}
                    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.5 }}
                      className="bg-white/[0.03] border border-gray-700/50 rounded-2xl p-4">
                      <div className="flex flex-wrap gap-4 justify-between items-center text-xs text-site-text-muted">
                        <div className="flex items-center gap-2">
                          <span className="font-bold uppercase tracking-wider">Backend:</span>
                          <span className="px-2 py-0.5 rounded bg-white/10 font-mono">{result.backend_used.toUpperCase()}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold uppercase tracking-wider">TTA:</span>
                          <span className={`px-2 py-0.5 rounded ${result.tta_used ? 'bg-[#7ed957]/20 text-[#7ed957]' : 'bg-white/10'}`}>
                            {result.tta_used ? 'ON (8 views)' : 'OFF'}
                          </span>
                        </div>
                        {inferenceTime > 0 && (
                          <div className="flex items-center gap-2">
                            <span className="font-bold uppercase tracking-wider">Time:</span>
                            <span className="px-2 py-0.5 rounded bg-white/10 font-mono">{inferenceTime}ms</span>
                          </div>
                        )}
                      </div>
                    </motion.div>

                  </motion.div>
                )}
              </AnimatePresence>

              {/* Pipeline info card (visible when no results) */}
              {stage !== 'results' && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.6 }}
                  className="bg-white/[0.03] border border-gray-700/50 rounded-2xl p-5">
                  <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted mb-3">3-Stage Pipeline</p>
                  <div className="space-y-3">
                    {[
                      { num: '1', title: 'Type Classification', desc: 'EfficientNet-B3 — identifies HDPE, LDPE, PET, PP, PS, or Other', color: '#7ed957' },
                      { num: '2', title: 'Recyclability Grade', desc: 'CLIP ViT-B/32 zero-shot — assigns Grade A, B, or C', color: '#f59e0b' },
                      { num: '3', title: 'Volumetric Estimation', desc: 'Depth Anything V2 — estimates volume in cm³', color: '#52a8db' },
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
