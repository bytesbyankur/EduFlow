import React from 'react';
import { ShieldCheck, AlertTriangle, CheckCircle2, TrendingUp } from 'lucide-react';

export default function AttendanceCalculator({ present = 0, total = 30 }) {
  const TARGET = Math.ceil(total * 0.75); // 75% requirement (e.g. 23 of 30)
  const isSafe = present >= TARGET;
  const needed = Math.max(0, TARGET - present);
  const percentage = Math.min(Math.round((present / TARGET) * 100), 100);
  const rawOverallPercent = total > 0 ? Math.round((present / total) * 100) : 0;

  return (
    <div style={{
      background: isSafe 
        ? 'linear-gradient(135deg, rgba(6, 78, 59, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%)' 
        : 'linear-gradient(135deg, rgba(30, 27, 75, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%)',
      border: isSafe 
        ? '1px solid rgba(16, 185, 129, 0.3)' 
        : '1px solid rgba(99, 102, 241, 0.25)',
      borderRadius: 'var(--radius-lg)',
      padding: '1.25rem',
      boxShadow: isSafe ? '0 8px 24px -4px rgba(16, 185, 129, 0.15)' : 'var(--shadow-md)',
      transition: 'all var(--transition-normal)'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{
            width: '2.25rem',
            height: '2.25rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: isSafe ? 'rgba(16, 185, 129, 0.2)' : 'rgba(99, 102, 241, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: isSafe ? '#34d399' : '#a5b4fc'
          }}>
            {isSafe ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          </div>
          <div>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
              75% Eligibility Meter
            </span>
            <h4 style={{ fontSize: '1rem', fontWeight: 800, color: '#ffffff' }}>
              {isSafe ? 'Threshold Cleared 🎉' : `Attend ${needed} More Classes`}
            </h4>
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          <span style={{
            fontSize: '0.7rem',
            fontWeight: 800,
            padding: '0.2rem 0.55rem',
            borderRadius: 'var(--radius-full)',
            backgroundColor: isSafe ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
            color: isSafe ? '#34d399' : '#fbbf24',
            border: isSafe ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)'
          }}>
            {isSafe ? 'SAFE' : 'ACTION REQUIRED'}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{ marginBottom: '0.85rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
          <span>Current: <strong>{present}</strong> sessions</span>
          <span>Target (75%): <strong>{TARGET}</strong> sessions</span>
        </div>

        <div style={{
          width: '100%',
          height: '10px',
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          borderRadius: 'var(--radius-full)',
          overflow: 'hidden',
          border: '1px solid var(--border-subtle)',
          position: 'relative'
        }}>
          <div style={{
            width: `${percentage}%`,
            height: '100%',
            background: isSafe 
              ? 'linear-gradient(90deg, #10b981 0%, #34d399 100%)' 
              : 'linear-gradient(90deg, #6366f1 0%, #818cf8 100%)',
            borderRadius: 'var(--radius-full)',
            transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
            boxShadow: isSafe ? '0 0 10px rgba(16, 185, 129, 0.5)' : '0 0 10px rgba(99, 102, 241, 0.4)'
          }} />
        </div>
      </div>

      {/* Explanatory Message */}
      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
        {isSafe 
          ? `Outstanding! You have attended ${present} out of ${total} total semester sessions. Your attendance rate (${rawOverallPercent}%) exceeds the 75% academic requirement.`
          : `To reach 75% exam eligibility, you must attend at least ${needed} more classes. Keeping regular attendance avoids academic debarment.`
        }
      </p>
    </div>
  );
}
