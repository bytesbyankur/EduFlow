import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Camera, X, CheckCircle2, AlertCircle, RefreshCw, Sparkles, ShieldCheck } from 'lucide-react';
import confetti from 'canvas-confetti';
import api from '../services/api';

export default function CameraScannerModal({ isOpen, onClose, currentClass, onAttendanceSuccess }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);

  const [scanStatus, setScanStatus] = useState('initializing');
  const [statusMessage, setStatusMessage] = useState('Accessing camera feed...');
  const [verifiedStudents, setVerifiedStudents] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);

  // Start Camera
  const startCamera = useCallback(async () => {
    try {
      setScanStatus('initializing');
      setStatusMessage('Requesting camera permissions...');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
      });
      
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setCameraActive(true);
        setScanStatus('scanning');
        setStatusMessage(`Active scan for: ${currentClass}`);
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

  // Perform single scan frame
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
          if (res.status === 'success' && res.students && res.students.length > 0) {
            setScanStatus('verified');
            setVerifiedStudents(res.students);
            setStatusMessage(`Verified: ${res.students.join(', ')}`);

            // Trigger celebration confetti
            try {
              confetti({
                particleCount: 50,
                spread: 60,
                origin: { y: 0.7 }
              });
            } catch {}

            if (onAttendanceSuccess) {
              onAttendanceSuccess(res.students, currentClass);
            }

            // Return to scanning after 3.5 seconds
            setTimeout(() => {
              setScanStatus('scanning');
              setStatusMessage(`Active scan for: ${currentClass}`);
            }, 3500);

          } else if (res.status === 'failed') {
            if (res.message && res.message.toLowerCase().includes('not found')) {
              setScanStatus('warning');
              setStatusMessage('Student not enrolled in this course roster');
            } else if (res.message && res.message.toLowerCase().includes('error')) {
              setScanStatus('error');
              setStatusMessage(res.message);
            } else {
              setScanStatus('scanning');
              setStatusMessage(res.message || `Scanning for ${currentClass}...`);
            }
          }
        } catch (err) {
          console.warn('Scan frame response error:', err.message);
        } finally {
          setIsProcessing(false);
        }
      }, 'image/jpeg', 0.85);
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

  // Set up auto-scan interval every 3.5 seconds
  useEffect(() => {
    if (isOpen && cameraActive) {
      intervalRef.current = setInterval(captureAndScan, 3500);
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
          maxWidth: '560px',
          backgroundColor: '#0f172a',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
          padding: '1.75rem',
          position: 'relative'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: '2.5rem',
              height: '2.5rem',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(79, 70, 229, 0.4)'
            }}>
              <Camera size={20} color="#ffffff" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff' }}>
                Face Attendance Scanner
              </h3>
              <p style={{ fontSize: '0.75rem', color: '#818cf8', fontWeight: 600 }}>
                Target Class: <strong>{currentClass}</strong>
              </p>
            </div>
          </div>

          <button 
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              width: '2rem',
              height: '2rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-secondary)',
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
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.6)'
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
            inset: '15%',
            border: scanStatus === 'verified' 
              ? '2px solid #10b981' 
              : scanStatus === 'warning' 
                ? '2px solid #f59e0b' 
                : '2px dashed rgba(99, 102, 241, 0.5)',
            borderRadius: 'var(--radius-lg)',
            pointerEvents: 'none',
            transition: 'border-color 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {scanStatus === 'verified' && (
              <div style={{
                backgroundColor: 'rgba(16, 185, 129, 0.9)',
                color: '#ffffff',
                padding: '0.5rem 1rem',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.85rem',
                fontWeight: 800,
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)'
              }}>
                <CheckCircle2 size={18} />
                <span>Attendance Logged!</span>
              </div>
            )}
          </div>

          {/* Top-right mode badge */}
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            backgroundColor: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(8px)',
            color: '#a5b4fc',
            padding: '0.3rem 0.65rem',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.7rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: '#10b981',
              boxShadow: '0 0 8px #10b981'
            }} />
            Auto-Scan Active (3.5s)
          </div>
        </div>

        {/* Live Status Bar */}
        <div style={{
          marginTop: '1.25rem',
          padding: '0.85rem 1rem',
          borderRadius: 'var(--radius-md)',
          backgroundColor: scanStatus === 'verified' 
            ? 'rgba(16, 185, 129, 0.12)' 
            : scanStatus === 'warning' 
              ? 'rgba(245, 158, 11, 0.12)' 
              : scanStatus === 'error'
                ? 'rgba(244, 63, 94, 0.12)'
                : 'rgba(99, 102, 241, 0.1)',
          border: scanStatus === 'verified'
            ? '1px solid rgba(16, 185, 129, 0.3)'
            : scanStatus === 'warning'
              ? '1px solid rgba(245, 158, 11, 0.3)'
              : scanStatus === 'error'
                ? '1px solid rgba(244, 63, 94, 0.3)'
                : '1px solid rgba(99, 102, 241, 0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          transition: 'all 0.3s ease'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            {scanStatus === 'verified' ? (
              <CheckCircle2 size={18} color="#34d399" />
            ) : scanStatus === 'warning' ? (
              <AlertCircle size={18} color="#fbbf24" />
            ) : scanStatus === 'error' ? (
              <AlertCircle size={18} color="#f87171" />
            ) : (
              <RefreshCw size={16} color="#818cf8" style={{ animation: isProcessing ? 'spin 1s linear infinite' : 'none' }} />
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
              padding: '0.45rem 0.95rem',
              fontSize: '0.75rem',
              borderRadius: 'var(--radius-md)',
              opacity: isProcessing ? 0.7 : 1
            }}
          >
            {isProcessing ? 'Analyzing...' : 'Scan Frame'}
          </button>
        </div>

        {/* Footer controls */}
        <div style={{
          marginTop: '1rem',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '0.75rem'
        }}>
          <button onClick={onClose} className="btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.8rem' }}>
            Done Scanning
          </button>
        </div>
      </div>
    </div>
  );
}
