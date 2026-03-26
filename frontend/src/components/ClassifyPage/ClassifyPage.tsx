import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { mockClassify, RECYCLING_TIPS } from '../../utils/mockInference';
import type { InferenceResult } from '../../utils/mockInference';

type Stage = 'upload' | 'scanning' | 'results';
type InputMode = 'upload' | 'webcam';

interface CameraDevice {
  deviceId: string;
  label: string;
}

const ClassifyPage = () => {
  const [stage, setStage] = useState<Stage>('upload');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string>('');
  const [result, setResult] = useState<InferenceResult | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [inputMode, setInputMode] = useState<InputMode>('upload');
  const [webcamActive, setWebcamActive] = useState(false);
  const [cameras, setCameras] = useState<CameraDevice[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const navigate = useNavigate();

  // Enumerate cameras when webcam mode is selected
  useEffect(() => {
    if (inputMode !== 'webcam') return;
    const listCameras = async () => {
      try {
        // Need temp permission to get labels
        const tempStream = await navigator.mediaDevices.getUserMedia({ video: true });
        const devices = await navigator.mediaDevices.enumerateDevices();
        tempStream.getTracks().forEach((t) => t.stop());
        const videoDevices = devices
          .filter((d) => d.kind === 'videoinput')
          .map((d, i) => ({
            deviceId: d.deviceId,
            label: d.label || `Camera ${i + 1}`,
          }));
        setCameras(videoDevices);
        // Auto-select the first camera (usually the laptop built-in)
        if (videoDevices.length > 0 && !selectedCamera) {
          setSelectedCamera(videoDevices[0].deviceId);
        }
      } catch {
        // Permission denied — will show error when they click start
      }
    };
    listCameras();
  }, [inputMode, selectedCamera]);

  // Cleanup webcam on unmount or mode switch
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
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
      // Use exact deviceId to lock to the selected camera
      const constraints: MediaStreamConstraints = {
        video: selectedCamera
          ? { deviceId: { exact: selectedCamera }, width: { ideal: 1280 }, height: { ideal: 720 } }
          : { width: { ideal: 1280 }, height: { ideal: 720 } },
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play();
        };
      }
      setWebcamActive(true);
    } catch {
      alert('Could not access webcam. Please check browser permissions and ensure no other app is using the camera.');
    }
  }, [selectedCamera]);

  const captureWebcam = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Use actual video stream dimensions
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    if (!vw || !vh) {
      alert('Camera not ready yet. Please wait a moment and try again.');
      return;
    }

    canvas.width = vw;
    canvas.height = vh;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, vw, vh);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' });
        setImageFile(file);
        setImageUrl(URL.createObjectURL(blob));
        stopWebcam();
        setStage('upload');
        setResult(null);
      },
      'image/jpeg',
      0.92
    );
  }, [stopWebcam]);

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) return;
    setImageFile(file);
    setImageUrl(URL.createObjectURL(file));
    setStage('upload');
    setResult(null);
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
    const res = await mockClassify(imageFile);
    setResult(res);
    setStage('results');
  };

  const handleReset = () => {
    setStage('upload');
    setImageFile(null);
    setImageUrl('');
    setResult(null);
  };

  const switchMode = (mode: InputMode) => {
    handleReset();
    if (mode === 'upload') stopWebcam();
    setInputMode(mode);
  };

  // Group detections by class for summary
  const classSummary = result?.detections.reduce(
    (acc, d) => {
      if (!acc[d.className]) acc[d.className] = { count: 0, totalConf: 0, color: d.color };
      acc[d.className].count += 1;
      acc[d.className].totalConf += d.confidence;
      return acc;
    },
    {} as Record<string, { count: number; totalConf: number; color: string }>
  );

  return (
    <div className="min-h-screen bg-site-black text-site-text-light">
      {/* Top bar */}
      <div className="w-full bg-site-dark text-site-text-light text-center py-2 text-xs md:text-sm tracking-widest uppercase font-medium">
        🔬 AI Plastic Waste Classification Engine
      </div>

      {/* Toggle navbar — centered */}
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
          <button
            className="relative px-6 py-2.5 rounded-full text-xs font-bold tracking-widest uppercase transition-all duration-300 text-black"
          >
            <motion.div
              layoutId="nav-pill"
              className="absolute inset-0 bg-[#7ed957] rounded-full"
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
            <span className="relative z-10">Classify</span>
          </button>
        </div>
      </motion.nav>

      {/* Hero header */}
      <section className="pt-28 pb-10 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="section-container"
        >
          <p className="text-[#7ed957] text-xs md:text-sm uppercase tracking-[0.3em] mb-4 font-bold">
            Core Feature
          </p>
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-black tracking-tight mb-4 leading-tight">
            Classify Your{' '}
            <span className="bg-gradient-to-r from-[#7ed957] to-[#5cb83f] bg-clip-text text-transparent">
              Plastic
            </span>
          </h1>
          <p className="text-sm md:text-base text-site-text-muted max-w-xl mx-auto leading-relaxed">
            Upload an image or use your webcam. Our YOLOv8 model detects and classifies
            every piece into PP, HDPE, PET, or Rigid — with confidence scores.
          </p>
        </motion.div>
      </section>

      {/* Main content */}
      <section className="pb-20">
        <div className="section-container">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            {/* LEFT — Input area */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              {/* Input mode toggle */}
              <div className="flex justify-center mb-6">
                <div className="bg-white/[0.05] rounded-full p-1 flex border border-gray-700/50">
                  <button
                    onClick={() => switchMode('upload')}
                    className={`px-5 py-2 rounded-full text-xs font-bold tracking-wider uppercase transition-all duration-300 ${
                      inputMode === 'upload'
                        ? 'bg-[#7ed957] text-black'
                        : 'text-site-text-muted hover:text-white'
                    }`}
                  >
                    📁 Upload
                  </button>
                  <button
                    onClick={() => switchMode('webcam')}
                    className={`px-5 py-2 rounded-full text-xs font-bold tracking-wider uppercase transition-all duration-300 ${
                      inputMode === 'webcam'
                        ? 'bg-[#7ed957] text-black'
                        : 'text-site-text-muted hover:text-white'
                    }`}
                  >
                    📷 Webcam
                  </button>
                </div>
              </div>

              {/* Upload mode */}
              {inputMode === 'upload' && !imageUrl && (
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                  }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`
                    relative cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-300
                    flex flex-col items-center justify-center min-h-[420px]
                    ${
                      isDragging
                        ? 'border-[#7ed957] bg-[#7ed957]/10 scale-[1.02]'
                        : 'border-gray-600 bg-white/[0.03] hover:border-gray-400 hover:bg-white/[0.05]'
                    }
                  `}
                >
                  <motion.div
                    animate={{ y: [0, -8, 0] }}
                    transition={{ repeat: Infinity, duration: 2.5, ease: 'easeInOut' }}
                    className="mb-6"
                  >
                    <svg
                      width="64"
                      height="64"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke={isDragging ? '#7ed957' : '#666'}
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </motion.div>
                  <p className="text-lg font-bold text-site-text-light mb-1">
                    {isDragging ? 'Drop it here!' : 'Drag & drop your image'}
                  </p>
                  <p className="text-sm text-site-text-muted">
                    or <span className="text-[#7ed957] underline">browse files</span>
                  </p>
                  <p className="text-xs text-site-text-muted/60 mt-3">JPG, PNG, BMP — up to 10 MB</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                    className="hidden"
                  />
                </div>
              )}

              {/* Webcam mode */}
              {inputMode === 'webcam' && !imageUrl && (
                <div className="rounded-2xl overflow-hidden bg-site-dark border border-gray-700/50">
                  <div className="relative min-h-[420px] flex items-center justify-center bg-black/50">
                    {!webcamActive ? (
                      <div className="text-center">
                        <motion.div
                          animate={{ scale: [1, 1.1, 1] }}
                          transition={{ repeat: Infinity, duration: 2 }}
                          className="mx-auto mb-4 w-20 h-20 rounded-full bg-white/10 flex items-center justify-center"
                        >
                          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#7ed957" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                            <circle cx="12" cy="13" r="4" />
                          </svg>
                        </motion.div>

                        {/* Camera selector */}
                        {cameras.length > 1 && (
                          <div className="mb-4">
                            <p className="text-xs text-site-text-muted mb-2 font-medium">Select Camera</p>
                            <select
                              value={selectedCamera}
                              onChange={(e) => setSelectedCamera(e.target.value)}
                              className="bg-white/10 text-white text-xs rounded-lg px-3 py-2 border border-gray-600 outline-none focus:border-[#7ed957] transition-colors w-64"
                            >
                              {cameras.map((cam) => (
                                <option key={cam.deviceId} value={cam.deviceId} className="bg-gray-900">
                                  {cam.label}
                                </option>
                              ))}
                            </select>
                          </div>
                        )}

                        <button
                          onClick={startWebcam}
                          className="px-6 py-3 bg-[#7ed957] text-black rounded-xl font-bold text-sm hover:bg-[#5cb83f] transition-all hover:scale-[1.02]"
                        >
                          Start Camera
                        </button>
                        <p className="text-xs text-site-text-muted/60 mt-3">
                          {cameras.length > 1 ? 'Select your laptop camera above, then start' : 'Allow camera access when prompted'}
                        </p>
                      </div>
                    ) : (
                      <>
                        <video
                          ref={videoRef}
                          autoPlay
                          playsInline
                          muted
                          className="w-full h-auto max-h-[420px] object-contain"
                        />
                        {/* Viewfinder corners */}
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
                      <button
                        onClick={captureWebcam}
                        className="flex-1 py-3 rounded-xl font-bold text-sm bg-[#7ed957] text-black hover:bg-[#5cb83f] transition-all hover:scale-[1.02] active:scale-[0.98]"
                      >
                        📸 Capture Photo
                      </button>
                      <button
                        onClick={stopWebcam}
                        className="px-4 py-3 rounded-xl font-bold text-sm bg-white/10 text-white hover:bg-white/20 transition-all"
                      >
                        ✕
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Image preview with overlays (shared for both modes) */}
              {imageUrl && (
                <div className="relative rounded-2xl overflow-hidden bg-site-dark border border-gray-700/50">
                  <div className="relative">
                    <img
                      src={imageUrl}
                      alt="Plastic to classify"
                      className="w-full h-auto max-h-[520px] object-contain bg-black/50"
                    />

                    {/* Scanning animation */}
                    <AnimatePresence>
                      {stage === 'scanning' && (
                        <>
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 bg-[#7ed957]/5"
                          />
                          <motion.div
                            initial={{ top: 0 }}
                            animate={{ top: '100%' }}
                            transition={{ duration: 1.8, repeat: Infinity, ease: 'linear' }}
                            className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#7ed957] to-transparent shadow-[0_0_20px_#7ed957]"
                          />
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: [0.3, 0.6, 0.3] }}
                            transition={{ duration: 1.5, repeat: Infinity }}
                            className="absolute inset-0 flex items-center justify-center"
                          >
                            <div className="bg-black/70 backdrop-blur-sm rounded-xl px-6 py-3">
                              <p className="text-[#7ed957] text-sm font-bold tracking-widest uppercase animate-pulse">
                                🔍 Analyzing...
                              </p>
                            </div>
                          </motion.div>
                        </>
                      )}
                    </AnimatePresence>

                    {/* Bounding box overlays */}
                    {stage === 'results' && result && (
                      <div className="absolute inset-0">
                        {result.detections.map((det, i) => (
                          <motion.div
                            key={i}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.4, delay: i * 0.15 }}
                            className="absolute"
                            style={{
                              left: `${det.bbox.x * 100}%`,
                              top: `${det.bbox.y * 100}%`,
                              width: `${det.bbox.w * 100}%`,
                              height: `${det.bbox.h * 100}%`,
                            }}
                          >
                            <div
                              className="w-full h-full border-2 rounded-md"
                              style={{
                                borderColor: det.color,
                                backgroundColor: `${det.color}15`,
                              }}
                            />
                            <div
                              className="absolute -top-6 left-0 px-2 py-0.5 rounded text-xs font-bold text-white whitespace-nowrap"
                              style={{ backgroundColor: det.color }}
                            >
                              {det.className} {(det.confidence * 100).toFixed(0)}%
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Action bar */}
                  <div className="p-4 flex gap-3 border-t border-gray-700/50">
                    {stage === 'upload' && (
                      <>
                        <button
                          onClick={handleAnalyze}
                          className="flex-1 py-3 rounded-xl font-bold text-sm bg-[#7ed957] text-black hover:bg-[#5cb83f] transition-all hover:scale-[1.02] active:scale-[0.98]"
                        >
                          🔍 Analyze Image
                        </button>
                        <button
                          onClick={handleReset}
                          className="px-4 py-3 rounded-xl font-bold text-sm bg-white/10 text-white hover:bg-white/20 transition-all"
                        >
                          ✕
                        </button>
                      </>
                    )}
                    {stage === 'scanning' && (
                      <div className="flex-1 py-3 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-[#7ed957] animate-pulse" />
                          <span className="text-sm text-site-text-muted font-medium">
                            Processing on GPU...
                          </span>
                        </div>
                      </div>
                    )}
                    {stage === 'results' && (
                      <>
                        <button
                          onClick={handleReset}
                          className="flex-1 py-3 rounded-xl font-bold text-sm bg-[#7ed957] text-black hover:bg-[#5cb83f] transition-all hover:scale-[1.02]"
                        >
                          ↻ Classify Another
                        </button>
                        <div className="px-4 py-3 rounded-xl bg-white/5 text-xs text-site-text-muted font-medium flex items-center">
                          {result?.inferenceTimeMs}ms
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </motion.div>

            {/* RIGHT — Results panel */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="space-y-4"
            >
              {/* Status card */}
              <div className="bg-white/[0.03] border border-gray-700/50 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      stage === 'results'
                        ? 'bg-[#7ed957]'
                        : stage === 'scanning'
                          ? 'bg-yellow-400 animate-pulse'
                          : 'bg-gray-500'
                    }`}
                  />
                  <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted">
                    {stage === 'upload'
                      ? 'Awaiting Image'
                      : stage === 'scanning'
                        ? 'Running Inference'
                        : 'Detection Complete'}
                  </p>
                </div>
                {stage === 'upload' && !imageUrl && (
                  <p className="text-sm text-site-text-muted leading-relaxed">
                    Upload an image or capture one from your webcam. The model will detect and classify each
                    piece individually, drawing bounding boxes with confidence scores.
                  </p>
                )}
                {stage === 'upload' && imageUrl && (
                  <p className="text-sm text-site-text-muted leading-relaxed">
                    Image loaded. Click{' '}
                    <span className="text-[#7ed957] font-semibold">Analyze Image</span> to run
                    detection.
                  </p>
                )}
                {stage === 'scanning' && (
                  <div className="space-y-3">
                    {[
                      'Loading model weights...',
                      'Preprocessing image (640×640)...',
                      'Running YOLOv8 inference...',
                    ].map((step, i) => (
                      <motion.div
                        key={step}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.5 }}
                        className="flex items-center gap-2"
                      >
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                          className="w-3 h-3 border-2 border-[#7ed957] border-t-transparent rounded-full"
                        />
                        <span className="text-xs text-site-text-muted">{step}</span>
                      </motion.div>
                    ))}
                  </div>
                )}
                {stage === 'results' && result && (
                  <div className="flex items-baseline gap-3">
                    <span className="text-5xl font-black text-[#7ed957]">
                      {result.detections.length}
                    </span>
                    <span className="text-sm text-site-text-muted font-medium">
                      plastic items detected
                    </span>
                  </div>
                )}
              </div>

              {/* Detection cards */}
              <AnimatePresence>
                {stage === 'results' && result && classSummary && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="space-y-3"
                  >
                    <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted px-1">
                      Detected Classes
                    </p>

                    {Object.entries(classSummary).map(([className, data], i) => (
                      <motion.div
                        key={className}
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4, delay: i * 0.12 }}
                        className="bg-white/[0.03] border border-gray-700/50 rounded-xl p-4 hover:border-gray-500 transition-all"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div
                              className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-black text-white"
                              style={{ backgroundColor: data.color }}
                            >
                              {className}
                            </div>
                            <div>
                              <p className="font-bold text-sm text-white">{className}</p>
                              <p className="text-xs text-site-text-muted">
                                {data.count} instance{data.count > 1 ? 's' : ''}
                              </p>
                            </div>
                          </div>
                          <span className="text-lg font-black" style={{ color: data.color }}>
                            {((data.totalConf / data.count) * 100).toFixed(1)}%
                          </span>
                        </div>

                        {/* Confidence bar */}
                        <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{
                              width: `${(data.totalConf / data.count) * 100}%`,
                            }}
                            transition={{ duration: 0.8, delay: 0.3 + i * 0.1, ease: 'easeOut' }}
                            className="h-full rounded-full"
                            style={{ backgroundColor: data.color }}
                          />
                        </div>

                        {/* Recycling tip */}
                        <p className="text-xs text-site-text-muted/70 mt-2 leading-relaxed">
                          {RECYCLING_TIPS[className] || 'Check local recycling guidelines.'}
                        </p>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Model info card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 }}
                className="bg-white/[0.03] border border-gray-700/50 rounded-2xl p-5"
              >
                <p className="text-xs font-bold tracking-widest uppercase text-site-text-muted mb-3">
                  Model Info
                </p>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    ['Architecture', 'YOLOv8s'],
                    ['Classes', '4 types'],
                    ['Input Size', '640×640'],
                    ['Framework', 'PyTorch'],
                  ].map(([label, value]) => (
                    <div key={label} className="bg-white/[0.03] rounded-lg p-3">
                      <p className="text-[10px] text-site-text-muted/60 uppercase tracking-wider font-medium">
                        {label}
                      </p>
                      <p className="text-sm font-bold text-white mt-0.5">{value}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default ClassifyPage;
