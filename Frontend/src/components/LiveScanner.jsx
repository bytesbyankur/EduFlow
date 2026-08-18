import React, { useState, useEffect, useRef, useCallback } from 'react';
import { scannerApi } from '../services/api';
import { Camera, CheckCircle2, RefreshCw, BookOpen, UserCheck, ShieldCheck, AlertCircle } from 'lucide-react';

const LiveScanner = ({ activeClass, onClassChange, onAttendanceMarked }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const isScanningRef = useRef(false);

  const [lastMatch, setLastMatch] = useState(null);
  const [matchDetails, setMatchDetails] = useState(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [scanStatus, setScanStatus] = useState("AI Biometrics Active (Scanning...)");

  // Start client webcam
  const startWebcam = async () => {
    try {
      setCameraError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
        audio: false,
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play().catch(e => console.error("Play error:", e));
          setIsCameraActive(true);
        };
      }
    } catch (err) {
      console.error("Camera access error:", err);
      setCameraError(err.message || "Failed to access webcam hardware");
      setIsCameraActive(false);
    }
  };

  // Stop client webcam
  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        try {
          track.stop();
        } catch (e) {
          console.error("Track stop error:", e);
        }
      });
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  // Lifecycle for webcam
  useEffect(() => {
    startWebcam();
    return () => {
      stopWebcam();
    };
  }, []);

  // Update backend when active course changes
  const handleCourseChange = async (e) => {
    const newClass = e.target.value;
    onClassChange(newClass);
    try {
      await scannerApi.setActiveClass(newClass);
    } catch (err) {
      console.error("Failed to update active class on backend:", err);
    }
  };

  // Continuous frame scanning loop
  // Continuous frame scanning loop
  const processFrame = useCallback(async () => {
    if (!videoRef.current || !isCameraActive || isScanningRef.current) return;
    const video = videoRef.current;
    if (video.readyState < 2) return; // HAVE_CURRENT_DATA

    isScanningRef.current = true;

    try {
      const canvas = canvasRef.current || document.createElement('canvas');
      canvas.width = 360;
      canvas.height = 270;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const base64Data = canvas.toDataURL('image/jpeg', 0.80);

      const response = await scannerApi.scanFrame({
        image: base64Data,
        class_name: activeClass,
      });

      const result = response.data || response;

      if (result.status === 'success' && (result.match || (result.matches && result.matches.length > 0))) {
        const verifiedNames = result.matches && result.matches.length > 1
          ? result.matches.join(', ')
          : (result.match || result.matches[0]);

        setLastMatch(verifiedNames);
        setMatchDetails(result);
        setScanStatus(`VERIFIED: ${verifiedNames.toUpperCase()} (Attendance Recorded)`);
        if (onAttendanceMarked) {
          onAttendanceMarked(result);
        }
      } else if (result.status === 'no_match') {
        setScanStatus("Face detected (Not enrolled in database)");
      } else {
        setScanStatus("Scanning for student faces...");
      }
    } catch (err) {
      // Background non-fatal scan error
    } finally {
      isScanningRef.current = false;
    }
  }, [activeClass, isCameraActive, onAttendanceMarked]);

  // Frame processing timer: ultra-fast 350ms loop
  useEffect(() => {
    if (!isCameraActive) return;
    const interval = setInterval(() => {
      processFrame();
    }, 350);

    return () => clearInterval(interval);
  }, [isCameraActive, processFrame]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl text-white">
      {/* Hidden canvas for snapshot extraction */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Header & Course Selector */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div>
          <h2 className="text-xl font-black flex items-center gap-2">
            <Camera className="text-indigo-400 w-6 h-6" />
            Live AI Biometric Scanner
          </h2>
          <p className="text-slate-400 text-xs font-medium mt-0.5">
            Real-time OpenCV & DeepFace biometric recognition
          </p>
        </div>

        <div className="flex items-center gap-3">
          <BookOpen className="text-indigo-400 w-5 h-5" />
          <select
            value={activeClass}
            onChange={handleCourseChange}
            className="bg-slate-800 border border-slate-700 text-white font-bold text-sm rounded-xl px-4 py-2.5 outline-none focus:border-indigo-500 transition-colors cursor-pointer"
          >
            <option value="Computer Vision 101">Computer Vision 101</option>
            <option value="Advanced Neural Networks">Advanced Neural Networks</option>
            <option value="Ethics in AI">Ethics in AI</option>
          </select>
        </div>
      </div>

      {/* Video Feed Screen */}
      <div className="relative w-full aspect-[4/3] max-h-[60vh] bg-black rounded-2xl overflow-hidden border border-slate-700 shadow-inner flex items-center justify-center">
        {/* HTML5 Live Video Element */}
        <video
          ref={videoRef}
          playsInline
          muted
          autoPlay
          className={`w-full h-full object-cover transform -scale-x-100 ${
            isCameraActive ? 'block' : 'hidden'
          }`}
        />

        {/* Camera Offline / Permission Error State */}
        {!isCameraActive && (
          <div className="text-center p-8 max-w-md">
            {cameraError ? (
              <>
                <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-3" />
                <p className="text-rose-400 font-black text-base mb-2">Camera Access Issue</p>
                <p className="text-slate-400 text-xs mb-5 leading-relaxed">{cameraError}</p>
              </>
            ) : (
              <>
                <RefreshCw className="w-10 h-10 text-indigo-400 animate-spin mx-auto mb-3" />
                <p className="text-slate-200 font-bold text-sm mb-2">Starting Camera Hardware...</p>
                <p className="text-slate-500 text-xs mb-4">Please allow camera permissions in your browser.</p>
              </>
            )}
            <button
              onClick={startWebcam}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-black uppercase tracking-wider inline-flex items-center gap-2 cursor-pointer transition-all shadow-lg shadow-indigo-900/40"
            >
              <RefreshCw className="w-4 h-4" /> Restart Camera
            </button>
          </div>
        )}

        {/* HUD Top Bar Overlay */}
        {isCameraActive && (
          <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/85 via-black/40 to-transparent p-4 sm:p-5 flex justify-between items-center pointer-events-none z-20">
            <div className="flex items-center gap-2.5">
              <span className="w-3 h-3 rounded-full bg-emerald-400 animate-ping"></span>
              <span className="text-xs font-black text-white tracking-widest uppercase">
                FULL-FRAME AI SCANNER
              </span>
            </div>
            <div className="bg-slate-900/90 backdrop-blur-md border border-slate-700/80 px-3.5 py-1.5 rounded-full text-xs font-bold text-slate-300 shadow-md">
              Class: <span className="text-indigo-400 font-black">{activeClass}</span>
            </div>
          </div>
        )}

        {/* Live Multi-Person Identified Badges on Scanning Window */}
        {isCameraActive && matchDetails?.matches && matchDetails.matches.length > 0 && (
          <div className="absolute top-16 left-4 right-4 flex flex-wrap gap-2 z-20 pointer-events-none animate-fade-in">
            {matchDetails.matches.map((name, idx) => (
              <div
                key={idx}
                className="flex items-center gap-1.5 bg-emerald-500 text-slate-950 px-3.5 py-1.5 rounded-xl text-xs font-black tracking-wide uppercase shadow-lg shadow-emerald-500/50 backdrop-blur-md border border-emerald-300"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-slate-950 shrink-0" />
                <span>{name}</span>
              </div>
            ))}
          </div>
        )}

        {/* Full-Frame Scanning Laser Beam & Corner Accents */}
        {isCameraActive && (
          <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden">
            {/* Viewport Corner Brackets */}
            <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-indigo-400/80 rounded-tl-lg"></div>
            <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-indigo-400/80 rounded-tr-lg"></div>
            <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-indigo-400/80 rounded-bl-lg"></div>
            <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-indigo-400/80 rounded-br-lg"></div>

            {/* Continuous Full-Width Scanning Line */}
            <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-pulse shadow-[0_0_12px_rgba(34,211,238,0.8)] opacity-90 my-auto"></div>

            {/* Bottom Status Pill */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-slate-950/90 backdrop-blur-md border border-slate-800 px-4 py-1.5 rounded-full text-[11px] font-black uppercase tracking-wider text-slate-200 shadow-lg text-center max-w-[90%] truncate">
              {scanStatus}
            </div>
          </div>
        )}

        {/* Real-time Match Notification Overlay */}
        {lastMatch && (
          <div className="absolute bottom-6 left-6 right-6 bg-emerald-950/95 border border-emerald-400/80 backdrop-blur-xl text-emerald-200 p-4 sm:p-5 rounded-2xl flex items-center justify-between shadow-2xl transition-all animate-fade-in z-30">
            <div className="flex items-center gap-3.5">
              <div className="p-3 bg-emerald-500/20 text-emerald-300 rounded-xl border border-emerald-500/40">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <p className="text-[10px] font-black text-emerald-300 uppercase tracking-widest">
                  Biometric Verified • {matchDetails?.confidence || 98}% Match{matchDetails?.matches?.length > 1 ? ` (${matchDetails.matches.length} Persons)` : ''}
                </p>
                <p className="text-lg font-black text-white">{lastMatch}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-black bg-emerald-500 text-slate-950 px-4 py-2 rounded-xl uppercase tracking-wider shadow-lg shadow-emerald-500/30 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" /> Present
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveScanner;