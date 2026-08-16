import React, { useRef, useState, useEffect } from 'react';
import { UserPlus, Camera, Upload, X, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import api from '../services/api';

export default function RegisterStudentModal({ isOpen, onClose, courses = [], onStudentRegistered }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const [name, setName] = useState('');
  const [selectedClass, setSelectedClass] = useState('');
  const [photoBlob, setPhotoBlob] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [mode, setMode] = useState('camera'); // 'camera' or 'upload'
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Sync default class when courses prop is passed
  useEffect(() => {
    if (courses.length > 0 && !selectedClass) {
      setSelectedClass(courses[0]);
    }
  }, [courses, selectedClass]);

  // Start Camera
  const startCamera = async () => {
    try {
      setErrorMsg('');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (err) {
      console.error('Camera access error:', err);
      setErrorMsg(`Camera error: ${err.message}. You can also use the File Upload mode.`);
    }
  };

  // Stop Camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  useEffect(() => {
    if (isOpen && mode === 'camera') {
      startCamera();
    } else {
      stopCamera();
    }
    return () => {
      stopCamera();
    };
  }, [isOpen, mode]);

  // Capture Snapshot from video
  const takeSnapshot = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(blob => {
      if (blob) {
        setPhotoBlob(blob);
        setPhotoPreview(URL.createObjectURL(blob));
      }
    }, 'image/jpeg', 0.9);
  };

  // Handle file upload
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPhotoBlob(file);
      setPhotoPreview(URL.createObjectURL(file));
    }
  };

  // Retake photo
  const retakePhoto = () => {
    setPhotoBlob(null);
    setPhotoPreview(null);
    setErrorMsg('');
    setSuccessMsg('');
  };

  // Submit registration
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMsg('Please enter the student full name');
      return;
    }
    if (!selectedClass) {
      setErrorMsg('Please select a course to enroll');
      return;
    }
    if (!photoBlob) {
      setErrorMsg('Please capture or upload a face photograph');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const res = await api.registerStudent(name.trim(), selectedClass, photoBlob);
      if (res.status === 'success') {
        setSuccessMsg(res.message || 'Student enrolled and biometric profile saved!');
        if (onStudentRegistered) {
          onStudentRegistered({ name: name.trim(), class_name: selectedClass });
        }
        setTimeout(() => {
          handleClose();
        }, 2500);
      } else {
        setErrorMsg(res.message || 'Registration failed');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to connect to backend server');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    stopCamera();
    setName('');
    setPhotoBlob(null);
    setPhotoPreview(null);
    setErrorMsg('');
    setSuccessMsg('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={handleClose}>
      <div 
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '540px',
          backgroundColor: '#0f172a',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
          padding: '1.75rem',
          position: 'relative'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: '2.5rem',
              height: '2.5rem',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)'
            }}>
              <UserPlus size={20} color="#ffffff" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff' }}>
                Register New Student
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Capture biometrics & enroll in courses
              </p>
            </div>
          </div>

          <button 
            onClick={handleClose}
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
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Feedback alerts */}
        {errorMsg && (
          <div style={{
            backgroundColor: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem 1rem',
            marginBottom: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            color: '#fda4af',
            fontSize: '0.825rem'
          }}>
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div style={{
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem 1rem',
            marginBottom: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            color: '#6ee7b7',
            fontSize: '0.825rem'
          }}>
            <CheckCircle2 size={16} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              Student Full Name
            </label>
            <input
              type="text"
              className="input-control"
              placeholder="e.g. John Doe"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              Assign to Course
            </label>
            <select
              className="select-control"
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              required
            >
              {courses.map((course, idx) => (
                <option key={idx} value={course} style={{ backgroundColor: '#0f172a', color: '#ffffff' }}>
                  {course}
                </option>
              ))}
            </select>
          </div>

          {/* Capture Mode Switcher */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                Face Biometrics Photo
              </span>
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                <button
                  type="button"
                  onClick={() => { setMode('camera'); retakePhoto(); }}
                  style={{
                    backgroundColor: mode === 'camera' ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
                    border: '1px solid ' + (mode === 'camera' ? '#6366f1' : 'var(--border-subtle)'),
                    color: mode === 'camera' ? '#a5b4fc' : 'var(--text-muted)',
                    padding: '0.2rem 0.6rem',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  <Camera size={12} style={{ display: 'inline', marginRight: '4px' }} />
                  Webcam
                </button>
                <button
                  type="button"
                  onClick={() => { setMode('upload'); stopCamera(); }}
                  style={{
                    backgroundColor: mode === 'upload' ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
                    border: '1px solid ' + (mode === 'upload' ? '#6366f1' : 'var(--border-subtle)'),
                    color: mode === 'upload' ? '#a5b4fc' : 'var(--text-muted)',
                    padding: '0.2rem 0.6rem',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  <Upload size={12} style={{ display: 'inline', marginRight: '4px' }} />
                  Upload
                </button>
              </div>
            </div>

            {/* Photo Capture / Preview Box */}
            <div style={{
              width: '100%',
              height: '200px',
              backgroundColor: '#020617',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px dashed rgba(255, 255, 255, 0.15)'
            }}>
              {photoPreview ? (
                <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                  <img
                    src={photoPreview}
                    alt="Preview"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                  <button
                    type="button"
                    onClick={retakePhoto}
                    style={{
                      position: 'absolute',
                      top: '8px',
                      right: '8px',
                      backgroundColor: 'rgba(0, 0, 0, 0.75)',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: 'var(--radius-sm)',
                      padding: '0.25rem 0.5rem',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    Retake
                  </button>
                </div>
              ) : mode === 'camera' ? (
                <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                  <video
                    ref={videoRef}
                    playsInline
                    muted
                    style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }}
                  />
                  <button
                    type="button"
                    onClick={takeSnapshot}
                    className="btn-emerald"
                    style={{
                      position: 'absolute',
                      bottom: '10px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      padding: '0.45rem 1.15rem',
                      fontSize: '0.75rem',
                      borderRadius: 'var(--radius-full)'
                    }}
                  >
                    <Camera size={14} />
                    <span>Snap Photo</span>
                  </button>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '1rem' }}>
                  <Upload size={28} color="#64748b" style={{ margin: '0 auto 0.5rem' }} />
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                    Select a clear face image (JPG/PNG)
                  </p>
                  <label className="btn-secondary" style={{ cursor: 'pointer', padding: '0.45rem 0.85rem', fontSize: '0.75rem' }}>
                    <span>Browse Image</span>
                    <input type="file" accept="image/*" onChange={handleFileUpload} style={{ display: 'none' }} />
                  </label>
                </div>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.75rem' }}>
            <button
              type="button"
              onClick={handleClose}
              className="btn-secondary"
              style={{ padding: '0.65rem 1.25rem' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !photoBlob}
              className="btn-primary"
              style={{
                padding: '0.65rem 1.5rem',
                opacity: isSubmitting || !photoBlob ? 0.6 : 1
              }}
            >
              {isSubmitting ? (
                <>
                  <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} />
                  <span>Processing AI Biometrics...</span>
                </>
              ) : (
                <>
                  <UserPlus size={16} />
                  <span>Capture & Save Student</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
