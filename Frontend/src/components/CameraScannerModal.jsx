import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Camera, X, CheckCircle2, AlertCircle, RefreshCw, Sparkles, ShieldCheck, Cpu, Zap, Activity } from 'lucide-react';
import confetti from 'canvas-confetti';
import api from '../services/api';

export default function CameraScannerModal({ isOpen, onClose, currentClass, onAttendanceSuccess }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);

  const [scanStatus, setScanStatus] = useState('initializing'); // 'initializing' | 'scanning' | 'verified' | 'warning' | 'error'
  const [statusMessage, setStatusMessage] = useState('Accessing camera feed...');
  const [verifiedStudents, setVerifiedStudents] = useState([]);
  const [matchDetails, setMatchDetails] = useState([]);
  const [confidenceScore, setConfidenceScore] = useState(0);
  const [inferenceLatency, setInferenceLatency] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [modelName, setModelName] = useState('LightweightFaceNet-v2');

  // Start Camera
  const startCamera = useCallback(async () => {
    try {
      setScanStatus('initializing');
      setStatusMessage('Initializing Camera & Neural Engine...');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
      });
      
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setCameraActive(true);
        setScanStatus('scanning');
        setStatusMessage(`Scanning faces for ${currentClass}...`);
      }
    } catch (err) {
      console.error('Camera access error:', err);
      setScanStatus('error');
      setStatusMessage(`Camera access failed: ${err.message || 'Permission denied'}`);
    }
  }, [currentClass]);

  // Stop Camera & Scan Loop
  const stopCamera = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  }, []);

  // Perform single scan frame with LightweightFaceNet NN
  const captureAndScan = useCallback(async () => {
    if (!videoRef.current || isProcessing || !cameraActive) return;

    const video = videoRef.current;
    if (video.videoWidth === 0 || video.videoHeight === 0) return;

    setIsProcessing(true);

    try {
      const canvas = document.createElement('canvas');
      const scale = Math.min(1, 640 / Math.max(video.videoWidth, video.videoHeight));
      canvas.width = Math.round(video.videoWidth * scale);
      canvas.height = Math.round(video.videoHeight * scale);
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      canvas.toBlob(async (blob) => {
        if (!blob) {
          setIsProcessing(false);
          return;
        }

        try {
          const res = await api.markAttendance(currentClass, blob);
          
          if (res.inference_time_ms) {
            setInferenceLatency(res.inference_time_ms);
          }
          if (res.model) {
            setModelName(res.model);
          }

          if (res.status === 'success' && res.students && res.students.length > 0) {
            // Deduplicate students list
            const uniqueStudents = Array.from(new Set(res.students));
            const conf = res.confidence || 95.0;
            const faceCount = res.faces_detected || uniqueStudents.length;

            setScanStatus('verified');
            setVerifiedStudents(uniqueStudents);
            setMatchDetails(res.matches || []);
            setConfidenceScore(conf);

            if (uniqueStudents.length === 1) {
              setStatusMessage(`Verified: ${uniqueStudents[0]} (${conf}% confidence)`);
            } else {
              setStatusMessage(`Verified (${uniqueStudents.length} Students): ${uniqueStudents.join(', ')} (${conf}% confidence)`);
            }

            // Trigger celebration confetti
            try {
              confetti({
                particleCount: 45,
                spread: 60,
                origin: { y: 0.7 }
              });
            } catch {}

            if (onAttendanceSuccess) {
              onAttendanceSuccess(uniqueStudents, currentClass);
            }

            // Return to scanning after 3.2 seconds
            setTimeout(() => {
              setScanStatus('scanning');
              setStatusMessage(`Scanning faces for ${currentClass}...`);
            }, 3200);

          } else if (res.status === 'failed') {
            const conf = res.confidence || 0;
            setConfidenceScore(conf);
            setMatchDetails(res.matches || []);

            if (res.message && res.message.toLowerCase().includes('not enrolled')) {
              setScanStatus('warning');
              setStatusMessage(res.message);
            } else if (res.message && res.message.toLowerCase().includes('no face')) {
              setScanStatus('scanning');
              setStatusMessage('No face in frame — please look directly at the scanner');
            } else if (res.message && res.message.toLowerCase().includes('low confidence')) {
              setScanStatus('warning');
              setStatusMessage(`Face detected with low confidence (${conf}%)`);
            } else {
              setScanStatus('warning');
              setStatusMessage(res.message || `Scanning for ${currentClass}...`);
            }
          }
        } catch (err) {
          console.warn('Scan frame response error:', err.message);
        } finally {
          setIsProcessing(false);
        }
      }, 'image/jpeg', 0.88);
    } catch (err) {
      console.error('Frame capture error:', err);
      setIsProcessing(false);
    }
  }, [currentClass, isProcessing, cameraActive, onAttendanceSuccess]);

  // Handle open/close lifecycle
  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => {
      stopCamera();
    };
  }, [isOpen, startCamera, stopCamera]);

  // Set up auto-scan interval every 2.8 seconds
  useEffect(() => {
    if (isOpen && cameraActive) {
      intervalRef.current = setInterval(captureAndScan, 2800);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isOpen, cameraActive, captureAndScan]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div 
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '600px',
          backgroundColor: '#090d16',
          border: '1px solid rgba(99, 102, 241, 0.35)',
          boxShadow: '0 25px 60px -12px rgba(0, 0, 0, 0.85)',
          padding: '1.75rem',
          position: 'relative',
          borderRadius: '1.25rem'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div style={{
              width: '2.75rem',
              height: '2.75rem',
              borderRadius: '0.85rem',
              background: 'linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 16px rgba(79, 70, 229, 0.45)'
            }}>
              <Camera size={22} color="#ffffff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
                  Neural Attendance Scanner
                </h3>
                <span style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  padding: '0.15rem 0.5rem',
                  borderRadius: '9999px',
                  backgroundColor: 'rgba(99, 102, 241, 0.2)',
                  color: '#a5b4fc',
                  border: '1px solid rgba(99, 102, 241, 0.4)'
                }}>
                  Lightweight NN
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: '#94a3b8', fontWeight: 500 }}>
                Target Class: <strong style={{ color: '#818cf8' }}>{currentClass}</strong>
              </p>
            </div>
          </div>

          <button 
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '0.5rem',
              width: '2.25rem',
              height: '2.25rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#94a3b8',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Video Camera Container */}
        <div style={{
          position: 'relative',
          width: '100%',
          aspectRatio: '4/3',
          backgroundColor: '#020617',
          borderRadius: '1rem',
          overflow: 'hidden',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: 'inset 0 2px 12px rgba(0, 0, 0, 0.8)'
        }}>
          <video
            ref={videoRef}
            playsInline
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transform: 'scaleX(-1)', // Mirror webcam
            }}
          />

          {/* Radar scanline animation */}
          {cameraActive && scanStatus === 'scanning' && (
            <div className="scan-radar" />
          )}

          {/* Facial targeting brackets */}
          <div style={{
            position: 'absolute',
            inset: '14%',
            border: scanStatus === 'verified' 
              ? '2px solid #10b981' 
              : scanStatus === 'warning' 
                ? '2px solid #f59e0b' 
                : '2px dashed rgba(99, 102, 241, 0.6)',
            borderRadius: '1rem',
            pointerEvents: 'none',
            transition: 'border-color 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {scanStatus === 'verified' && (
              <div style={{
                backgroundColor: 'rgba(16, 185, 129, 0.92)',
                color: '#ffffff',
                padding: '0.6rem 1.25rem',
                borderRadius: '9999px',
                fontSize: '0.9rem',
                fontWeight: 800,
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: '0 6px 20px rgba(16, 185, 129, 0.5)'
              }}>
                <CheckCircle2 size={20} />
                <span>Attendance Logged & Verified!</span>
              </div>
            )}
          </div>

          {/* Top telemetry badges */}
          <div style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            right: '12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            pointerEvents: 'none'
          }}>
            {/* Model Badge */}
            <div style={{
              backgroundColor: 'rgba(15, 23, 42, 0.75)',
              backdropFilter: 'blur(8px)',
              color: '#cbd5e1',
              padding: '0.3rem 0.65rem',
              borderRadius: '9999px',
              fontSize: '0.7rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              border: '1px solid rgba(255, 255, 255, 0.12)'
            }}>
              <Zap size={13} color="#38bdf8" />
              <span>{modelName}</span>
              {inferenceLatency > 0 && (
                <span style={{ color: '#38bdf8', borderLeft: '1px solid rgba(255,255,255,0.2)', paddingLeft: '0.35rem' }}>
                  {inferenceLatency}ms
                </span>
              )}
            </div>

            {/* Auto scan status */}
            <div style={{
              backgroundColor: 'rgba(15, 23, 42, 0.75)',
              backdropFilter: 'blur(8px)',
              color: '#a5b4fc',
              padding: '0.3rem 0.65rem',
              borderRadius: '9999px',
              fontSize: '0.7rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              border: '1px solid rgba(255, 255, 255, 0.12)'
            }}>
              <span style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: scanStatus === 'verified' ? '#10b981' : '#38bdf8',
                boxShadow: `0 0 8px ${scanStatus === 'verified' ? '#10b981' : '#38bdf8'}`
              }} />
              {isProcessing ? 'Analyzing Frame...' : 'Live Auto-Scan (2.8s)'}
            </div>
          </div>

          {/* Bottom confidence overlay if detected */}
          {confidenceScore > 0 && (
            <div style={{
              position: 'absolute',
              bottom: '12px',
              left: '12px',
              right: '12px',
              backgroundColor: 'rgba(15, 23, 42, 0.85)',
              backdropFilter: 'blur(10px)',
              padding: '0.6rem 0.85rem',
              borderRadius: '0.75rem',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.35rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
                <span style={{ color: '#94a3b8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Activity size={13} color="#818cf8" />
                  Neural Match Confidence
                </span>
                <span style={{
                  fontWeight: 800,
                  color: confidenceScore >= 80 ? '#34d399' : confidenceScore >= 60 ? '#fbbf24' : '#f87171'
                }}>
                  {confidenceScore}%
                </span>
              </div>
              <div style={{
                width: '100%',
                height: '6px',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '9999px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${Math.min(100, confidenceScore)}%`,
                  height: '100%',
                  background: confidenceScore >= 80 
                    ? 'linear-gradient(90deg, #10b981, #34d399)' 
                    : confidenceScore >= 60 
                      ? 'linear-gradient(90deg, #f59e0b, #fbbf24)' 
                      : 'linear-gradient(90deg, #ef4444, #f87171)',
                  borderRadius: '9999px',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
          )}
        </div>

        {/* Live Status Bar */}
        <div style={{
          marginTop: '1.15rem',
          padding: '0.85rem 1rem',
          borderRadius: '0.75rem',
          backgroundColor: scanStatus === 'verified' 
            ? 'rgba(16, 185, 129, 0.12)' 
            : scanStatus === 'warning' 
              ? 'rgba(245, 158, 11, 0.12)' 
              : scanStatus === 'error' 
                ? 'rgba(244, 63, 94, 0.12)' 
                : 'rgba(99, 102, 241, 0.1)',
          border: scanStatus === 'verified'
            ? '1px solid rgba(16, 185, 129, 0.35)'
            : scanStatus === 'warning'
              ? '1px solid rgba(245, 158, 11, 0.35)'
              : scanStatus === 'error'
                ? '1px solid rgba(244, 63, 94, 0.35)'
                : '1px solid rgba(99, 102, 241, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          transition: 'all 0.3s ease'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {scanStatus === 'verified' ? (
              <CheckCircle2 size={20} color="#34d399" />
            ) : scanStatus === 'warning' ? (
              <AlertCircle size={20} color="#fbbf24" />
            ) : scanStatus === 'error' ? (
              <AlertCircle size={20} color="#f87171" />
            ) : (
              <RefreshCw size={18} color="#818cf8" style={{ animation: isProcessing ? 'spin 1s linear infinite' : 'none' }} />
            )}
            <div>
              <p style={{
                fontSize: '0.85rem',
                fontWeight: 700,
                color: scanStatus === 'verified' ? '#34d399' : scanStatus === 'warning' ? '#fbbf24' : scanStatus === 'error' ? '#f87171' : '#e2e8f0'
              }}>
                {statusMessage}
              </p>
            </div>
          </div>

          <button
            onClick={captureAndScan}
            disabled={isProcessing || !cameraActive}
            className="btn-primary"
            style={{
              padding: '0.45rem 1rem',
              fontSize: '0.78rem',
              borderRadius: '0.5rem',
              opacity: isProcessing ? 0.7 : 1,
              whiteSpace: 'nowrap'
            }}
          >
            {isProcessing ? 'Analyzing...' : 'Scan Frame'}
          </button>
        </div>

        {/* Footer controls */}
        <div style={{
          marginTop: '1.15rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.72rem', color: '#64748b' }}>
            <Cpu size={14} color="#6366f1" />
            <span>Cosine Metric hypersphere matching (128D)</span>
          </div>

          <button onClick={onClose} className="btn-secondary" style={{ padding: '0.5rem 1.15rem', fontSize: '0.82rem' }}>
            Close Scanner
          </button>
        </div>
      </div>
    </div>
  );
}
