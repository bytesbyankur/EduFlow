import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  GraduationCap, 
  LogOut, 
  Sparkles, 
  ShieldCheck, 
  UserCheck, 
  BookOpen 
} from 'lucide-react';

export default function Navbar({ onNavigateLanding }) {
  const { user, logoutUser } = useAuth();

  const handleLogout = () => {
    logoutUser();
    if (onNavigateLanding) onNavigateLanding();
  };

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 40,
      width: '100%',
      backgroundColor: 'rgba(11, 17, 32, 0.85)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
      padding: '0.875rem 1.5rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      {/* Brand & AI Indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <div 
          onClick={onNavigateLanding}
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.75rem', 
            cursor: 'pointer',
            userSelect: 'none'
          }}
        >
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
            <GraduationCap size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.03em', color: '#ffffff' }}>
                Edu<span style={{ color: '#818cf8' }}>Flow</span>
              </span>
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                color: '#a5b4fc',
                padding: '0.15rem 0.45rem',
                borderRadius: 'var(--radius-full)',
                border: '1px solid rgba(99, 102, 241, 0.3)'
              }}>
                DJANGO AI
              </span>
            </div>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '-2px' }}>
              AI-Powered Attendance Intelligence
            </p>
          </div>
        </div>

        {/* AI Vision Status */}
        <div style={{
          display: 'none',
          alignItems: 'center',
          gap: '0.5rem',
          backgroundColor: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          padding: '0.35rem 0.75rem',
          borderRadius: 'var(--radius-full)',
          fontSize: '0.75rem',
          color: '#34d399',
          fontWeight: 600,
        }} className="desktop-ai-pill">
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: '#10b981',
            boxShadow: '0 0 8px #10b981',
            display: 'inline-block'
          }}></span>
          LightweightFaceNet NN Active
        </div>
      </div>

      {/* User Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {user ? (
          <>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              padding: '0.35rem 0.85rem 0.35rem 0.5rem',
              borderRadius: 'var(--radius-full)'
            }}>
              <div style={{
                width: '1.85rem',
                height: '1.85rem',
                borderRadius: '50%',
                backgroundColor: user.role === 'teacher' ? '#4f46e5' : '#059669',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                fontSize: '0.75rem',
                fontWeight: 700
              }}>
                {user.name ? user.name.charAt(0) : 'U'}
              </div>
              <div style={{ textAlign: 'left' }}>
                <p style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', lineHeight: 1.2 }}>
                  {user.name}
                </p>
                <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                  {user.role === 'teacher' ? 'Faculty Admin' : user.roll_number || 'Enrolled Student'}
                </p>
              </div>
            </div>

            <button 
              onClick={handleLogout}
              className="btn-secondary"
              style={{
                padding: '0.45rem 0.85rem',
                fontSize: '0.75rem',
                borderRadius: 'var(--radius-md)'
              }}
              title="Sign out of system"
            >
              <LogOut size={14} />
              <span>Logout</span>
            </button>
          </>
        ) : (
          <button 
            onClick={onNavigateLanding}
            className="btn-primary"
            style={{
              padding: '0.5rem 1.15rem',
              fontSize: '0.8rem'
            }}
          >
            <Sparkles size={15} />
            <span>Enter Experience</span>
          </button>
        )}
      </div>
    </header>
  );
}
