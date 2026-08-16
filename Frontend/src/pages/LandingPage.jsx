import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  BookOpen, 
  Cloud, 
  TrendingUp, 
  Sparkles, 
  ChevronRight, 
  ArrowLeft, 
  GraduationCap, 
  Mail, 
  Briefcase, 
  User, 
  Lock 
} from 'lucide-react';
import api from '../services/api';

export default function LandingPage({ onLoginSuccess }) {
  const { loginUser } = useAuth();

  const [activeSection, setActiveSection] = useState('welcome'); // 'welcome' or 'login'
  const [currentRole, setCurrentRole] = useState('teacher'); // 'teacher' or 'student'
  const [userId, setUserId] = useState('admin');
  const [password, setPassword] = useState('admin');
  const [isLoading, setIsLoading] = useState(false);
  const [showLoadingScreen, setShowLoadingScreen] = useState(false);
  const [parallax, setParallax] = useState({ x: 0, y: 0 });

  // Parallax mouse move effect
  useEffect(() => {
    const handleMouseMove = (e) => {
      const x = (e.clientX / window.innerWidth) * 20;
      const y = (e.clientY / window.innerHeight) * 20;
      setParallax({ x, y });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleRoleChange = (role) => {
    setCurrentRole(role);
    if (role === 'teacher') {
      setUserId('admin');
      setPassword('admin');
    } else {
      setUserId('REG-2025-001');
      setPassword('password123');
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();

    if (!userId || !password) {
      alert("Please enter both ID and Password.");
      return;
    }

    setIsLoading(true);

    try {
      const data = await api.login(userId.trim(), password.trim(), currentRole);

      if (data.status === 'success') {
        loginUser({
          name: data.name,
          role: data.role,
          roll_number: data.roll_number || userId.trim(),
        });

        setShowLoadingScreen(true);

        setTimeout(() => {
          setShowLoadingScreen(false);
          if (onLoginSuccess) {
            onLoginSuccess(data.role);
          }
        }, 1200);
      } else {
        alert("❌ Login Failed: " + (data.detail || data.message || "Invalid Credentials"));
      }
    } catch (err) {
      console.error("Login Failed:", err);
      alert("❌ Login Failed: " + (err.message || "Server error"));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-[#0a0f2b] overflow-hidden text-white font-sans">
      {/* Loading Screen Overlay */}
      {showLoadingScreen && (
        <div className="fixed inset-0 bg-[#0a0f2b] z-[100] flex flex-col items-center justify-center">
          <div className="w-20 h-20 border-t-4 border-l-4 border-purple-500 rounded-full animate-spin mb-8 shadow-[0_0_40px_rgba(168,85,247,0.3)]"></div>
          <p className="text-purple-300 font-black tracking-[0.5em] text-xs uppercase animate-pulse">
            Establishing Secure Uplink
          </p>
        </div>
      )}

      {/* SECTION 1: WELCOME PAGE */}
      {activeSection === 'welcome' && (
        <section className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden">
          <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-[#7c3aed]/10 blur-[140px] rounded-full pointer-events-none"></div>
          <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-[#1e1b4b]/40 blur-[140px] rounded-full pointer-events-none"></div>

          {/* Parallax Container */}
          <div 
            className="absolute inset-0 pointer-events-none"
            style={{ transform: `translate(${parallax.x}px, ${parallax.y}px)` }}
          >
            <div className="absolute top-[15%] left-[20%] floating-icon">
              <BookOpen className="text-purple-300 opacity-40 w-10 h-10" />
            </div>
            <div className="absolute top-[25%] right-[15%] floating-icon" style={{ animationDelay: '1s' }}>
              <Cloud className="text-purple-400 opacity-30 w-14 h-14" />
            </div>
            <div className="absolute bottom-[30%] left-[10%] floating-icon" style={{ animationDelay: '2s' }}>
              <TrendingUp className="text-blue-300 opacity-40 w-12 h-12" />
            </div>
            <div className="absolute bottom-[20%] right-[25%] floating-icon" style={{ animationDelay: '1.5s' }}>
              <Sparkles className="text-purple-200 opacity-50 w-8 h-8" />
            </div>
          </div>

          <div className="z-10 flex flex-col items-center justify-center text-center space-y-10 max-w-4xl">
            <div className="relative group">
              <div className="absolute inset-0 bg-purple-500 blur-[90px] opacity-10 group-hover:opacity-30 transition-opacity duration-700"></div>
              <h1 className="text-7xl md:text-[10rem] font-black tracking-tighter mb-0 flex cursor-default select-none relative">
                {"EduFlow".split("").map((char, i) => (
                  <span
                    key={i}
                    className="letter bg-clip-text text-transparent bg-gradient-to-b from-white via-purple-100 to-purple-400"
                    style={{ animationDelay: `${i * 0.1}s` }}
                  >
                    {char}
                  </span>
                ))}
              </h1>
            </div>

            <div className="space-y-4">
              <p className="text-2xl md:text-3xl text-purple-200 font-light tracking-wide italic tagline" style={{ animationDelay: '1.2s' }}>
                Your Unified Learning Hub
              </p>
              <p className="text-lg md:text-xl text-slate-400 font-medium tracking-normal tagline" style={{ animationDelay: '1.4s' }}>
                Making your university life <span className="text-[#d8b4fe] font-bold">easier than ever.</span>
              </p>
            </div>

            <div className="pt-8 tagline" style={{ animationDelay: '1.6s' }}>
              <button 
                onClick={() => setActiveSection('login')}
                className="glass-btn px-12 py-5 rounded-2xl flex items-center space-x-4 group cursor-pointer"
              >
                <span className="text-lg font-bold tracking-[0.2em] uppercase text-purple-50">
                  Enter Experience
                </span>
                <div className="w-10 h-10 rounded-full bg-[#7c3aed] flex items-center justify-center group-hover:bg-[#a855f7] transition-colors shadow-lg">
                  <ChevronRight className="w-6 h-6 group-hover:translate-x-1 transition-transform text-white" />
                </div>
              </button>
            </div>
          </div>

          <div className="absolute bottom-10 flex space-x-8 text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold tagline" style={{ animationDelay: '2s' }}>
            <span>Cloud Infrastructure</span>
            <span className="text-slate-700">•</span>
            <span>Attendance Intelligence</span>
            <span className="text-slate-700">•</span>
            <span>Academic Tracking</span>
          </div>
        </section>
      )}

      {/* SECTION 2: LOGIN PAGE */}
      {activeSection === 'login' && (
        <section className="min-h-screen flex flex-col items-center justify-center p-6 relative">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-600/10 blur-[120px] rounded-full pointer-events-none"></div>

          <button 
            onClick={() => setActiveSection('welcome')}
            className="absolute top-8 left-8 flex items-center text-slate-400 font-semibold hover:text-purple-300 transition-colors z-20 cursor-pointer"
          >
            <ArrowLeft className="mr-2 w-5 h-5" /> Back to Home
          </button>

          <div className="w-full max-w-md bg-white rounded-[40px] shadow-2xl overflow-hidden p-10 z-10 border border-slate-100 text-slate-900">
            <div className="text-center mb-10">
              <div className="w-20 h-20 bg-purple-50 text-purple-600 rounded-[24px] flex items-center justify-center mx-auto mb-6 shadow-sm border border-purple-100/50">
                <GraduationCap className="w-10 h-10" />
              </div>
              <h2 className="text-3xl font-black text-slate-900 tracking-tight">Portal Login</h2>
              <p className="text-slate-500 text-sm mt-2">Secure access to your academic ecosystem</p>
            </div>

            {/* Role Switcher */}
            <div className="flex bg-slate-100/80 p-1.5 rounded-2xl mb-10 border border-slate-200">
              <button
                type="button"
                onClick={() => handleRoleChange('teacher')}
                className={`flex-1 py-3 text-xs font-black tracking-widest uppercase rounded-xl transition-all cursor-pointer ${
                  currentRole === 'teacher'
                    ? 'bg-white text-indigo-700 shadow-md transform scale-105'
                    : 'text-slate-400 hover:bg-white/50'
                }`}
              >
                Faculty
              </button>
              <button
                type="button"
                onClick={() => handleRoleChange('student')}
                className={`flex-1 py-3 text-xs font-black tracking-widest uppercase rounded-xl transition-all cursor-pointer ${
                  currentRole === 'student'
                    ? 'bg-white text-purple-600 shadow-md transform scale-105'
                    : 'text-slate-400 hover:bg-white/50'
                }`}
              >
                Student
              </button>
            </div>

            <form onSubmit={handleAuth} className="space-y-6">
              <div className="space-y-5">
                <div>
                  <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3 ml-1">
                    {currentRole === 'teacher' ? 'Faculty ID' : 'Student Reg. Number'}
                  </label>
                  <div className="relative group">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-600 transition-colors">
                      {currentRole === 'teacher' ? <Briefcase className="w-5 h-5" /> : <User className="w-5 h-5" />}
                    </div>
                    <input
                      type="text"
                      required
                      value={userId}
                      onChange={(e) => setUserId(e.target.value)}
                      placeholder={currentRole === 'teacher' ? 'e.g. admin' : 'e.g. REG-2025-001'}
                      className={`w-full pl-12 pr-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-medium focus:ring-4 focus:bg-white outline-none transition-all ${
                        currentRole === 'teacher' 
                          ? 'focus:ring-indigo-100 focus:border-indigo-600' 
                          : 'focus:ring-purple-100 focus:border-purple-600'
                      }`}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3 ml-1">
                    Access Password
                  </label>
                  <div className="relative group">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-purple-600 transition-colors w-5 h-5" />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full pl-12 pr-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-medium focus:ring-4 focus:bg-white outline-none transition-all focus:ring-purple-100 focus:border-purple-600"
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs pt-2">
                <label className="flex items-center text-slate-500 cursor-pointer font-bold">
                  <input type="checkbox" defaultChecked className="mr-2 rounded-lg border-slate-300 text-purple-600 focus:ring-purple-600 h-4 w-4" />
                  Stay signed in
                </label>
                <span className={`font-black tracking-tight hover:underline cursor-pointer ${currentRole === 'teacher' ? 'text-indigo-600' : 'text-purple-600'}`}>
                  Recovery Account
                </span>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className={`w-full py-5 rounded-[20px] text-sm font-black text-white tracking-[0.2em] uppercase transition-all shadow-xl active:scale-[0.98] cursor-pointer ${
                  currentRole === 'teacher'
                    ? 'bg-gradient-to-r from-indigo-700 to-blue-800 hover:shadow-indigo-200'
                    : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:shadow-purple-200'
                }`}
                style={{ opacity: isLoading ? 0.7 : 1 }}
              >
                {isLoading ? 'VERIFYING...' : 'Authorize Entry'}
              </button>
            </form>

            <div className="mt-12 flex items-center justify-center space-x-4 opacity-40">
              <div className="h-[1px] w-8 bg-slate-300"></div>
              <span className="text-[10px] font-black text-slate-400 tracking-[0.3em]">SECURE NAVY CLOUD</span>
              <div className="h-[1px] w-8 bg-slate-300"></div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
