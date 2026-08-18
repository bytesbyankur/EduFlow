import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Cloud, 
  LayoutDashboard, 
  Users, 
  FolderOpen, 
  LogOut, 
  ChevronDown, 
  CheckCircle, 
  CheckSquare, 
  UploadCloud, 
  Download, 
  Plus, 
  FileText,
  Trash2,
  RotateCcw 
} from 'lucide-react';
import api from '../services/api';

export default function TeacherDashboard({ onSignOut }) {
  const { logoutUser } = useAuth();

  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard', 'students', 'cloud'
  const [currentClass, setCurrentClass] = useState('Advanced Neural Networks');
  const [classesList] = useState([
    'Advanced Neural Networks',
    'Ethics in AI',
    'Computer Vision 101'
  ]);
  const [rosterData, setRosterData] = useState({ count: 0, students: [], student_records: [] });
  const [allStudentsList, setAllStudentsList] = useState([]);
  const [directoryClassFilter, setDirectoryClassFilter] = useState('all');
  const [dashboardData, setDashboardData] = useState({
    stats: { total_students: 0, present_today: 0 },
    recent_logs: []
  });

  // Scanner Modal state & refs
  const [isScannerOpen, setIsScannerOpen] = useState(false);
  const [scanStatusText, setScanStatusText] = useState('Initializing Camera...');
  const [scanStatusHtml, setScanStatusHtml] = useState(null);
  const scannerVideoRef = useRef(null);
  const scannerStreamRef = useRef(null);
  const scanIntervalRef = useRef(null);

  // Registration Modal state & refs
  const [isRegModalOpen, setIsRegModalOpen] = useState(false);
  const [newStudentName, setNewStudentName] = useState('');
  const [newStudentClass, setNewStudentClass] = useState('Advanced Neural Networks');
  const [regProcessing, setRegProcessing] = useState(false);
  const regVideoRef = useRef(null);
  const regStreamRef = useRef(null);

  // Fetch Class Roster
  const fetchRoster = useCallback(async (className) => {
    try {
      const data = await api.getClassRoster(className);
      setRosterData(data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  // Fetch Directory Students (All or Class Specific)
  const fetchDirectoryStudents = useCallback(async (filter = 'all') => {
    try {
      if (filter === 'all') {
        const data = await api.getAllStudents();
        setAllStudentsList(data.student_records || []);
      } else {
        const data = await api.getClassRoster(filter);
        setAllStudentsList(data.student_records || []);
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  // Fetch Dashboard Stats & Recent Logs
  const fetchDashboard = useCallback(async () => {
    try {
      const data = await api.getDashboardData();
      setDashboardData(data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  // Class selection change handler
  const handleClassChange = (e) => {
    const selected = e.target.value;
    setCurrentClass(selected);
    fetchRoster(selected);
    fetchDashboard();
  };

  useEffect(() => {
    fetchRoster(currentClass);
    fetchDashboard();
    fetchDirectoryStudents(directoryClassFilter);
  }, [currentClass, directoryClassFilter, fetchRoster, fetchDashboard, fetchDirectoryStudents]);

  // Periodic refresh
  useEffect(() => {
    const interval = setInterval(() => {
      fetchDashboard();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  // --- SCANNER LOGIC ---
  const startScanner = async () => {
    setIsScannerOpen(true);
    setScanStatusHtml(null);
    setScanStatusText(`🔍 Scanning for ${currentClass}...`);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      scannerStreamRef.current = stream;
      if (scannerVideoRef.current) {
        scannerVideoRef.current.srcObject = stream;
        scannerVideoRef.current.play();
      }

      // Auto-scan interval (3s)
      scanIntervalRef.current = setInterval(() => {
        if (!scannerVideoRef.current) return;
        const video = scannerVideoRef.current;
        if (video.videoWidth === 0 || video.videoHeight === 0) return;

        // Downscale frame to 640x480 max for fast inference & minimal network payload
        const canvas = document.createElement('canvas');
        const scale = Math.min(1, 640 / Math.max(video.videoWidth, video.videoHeight));
        canvas.width = Math.round(video.videoWidth * scale);
        canvas.height = Math.round(video.videoHeight * scale);
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(blob => {
          if (!blob) return;
          api.markAttendance(currentClass, blob)
            .then(d => {
              if (d.status === 'success' && d.students && d.students.length > 0) {
                const uniqueStudents = Array.from(new Set(d.students));
                const conf = d.confidence || 95.0;
                const latency = d.inference_time_ms ? ` (${d.inference_time_ms}ms)` : '';
                setScanStatusHtml(
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-green-400 font-bold text-base">
                      ✅ Verified: {uniqueStudents.join(', ')}
                    </span>
                    <span className="text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1 rounded-full font-black">
                      ⚡ {conf}% Confidence {latency}
                    </span>
                  </div>
                );
                fetchDashboard();
              } else if (d.status === 'failed') {
                const conf = d.confidence > 0 ? ` (${d.confidence}% match)` : '';
                setScanStatusHtml(
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-yellow-400 font-bold">
                      ⚠️ {d.message || 'Face not recognized in this class'} {conf}
                    </span>
                    <span className="text-xs text-slate-400">
                      Looking for students enrolled in {currentClass}
                    </span>
                  </div>
                );
              }
            })
            .catch(err => {
              console.error(err);
            });
        }, 'image/jpeg', 0.85);
      }, 2800);

    } catch (err) {
      setScanStatusText('❌ Camera Error: ' + err.message);
    }
  };

  const stopScanner = () => {
    setIsScannerOpen(false);
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    if (scannerStreamRef.current) {
      scannerStreamRef.current.getTracks().forEach(t => t.stop());
      scannerStreamRef.current = null;
    }
  };

  // --- REGISTRATION LOGIC ---
  const openRegistrationModal = async () => {
    setIsRegModalOpen(true);
    setNewStudentName('');
    setNewStudentClass(currentClass);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      regStreamRef.current = stream;
      if (regVideoRef.current) {
        regVideoRef.current.srcObject = stream;
        regVideoRef.current.play();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const closeRegModal = () => {
    setIsRegModalOpen(false);
    if (regStreamRef.current) {
      regStreamRef.current.getTracks().forEach(t => t.stop());
      regStreamRef.current = null;
    }
  };

  const registerStudent = () => {
    if (!newStudentName.trim()) {
      alert("Please enter a name first!");
      return;
    }

    if (!regVideoRef.current) return;
    const video = regVideoRef.current;
    setRegProcessing(true);

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob(blob => {
      if (!blob) {
        setRegProcessing(false);
        return;
      }

      api.registerStudent(newStudentName.trim(), newStudentClass, blob)
        .then(data => {
          if (data.status === 'success') {
            alert(`✅ ${data.message}`);
            closeRegModal();
            fetchRoster(currentClass);
            fetchDashboard();
            fetchDirectoryStudents(directoryClassFilter);
          } else {
            alert("❌ Error: " + data.message);
          }
        })
        .catch(err => {
          alert("❌ Error: " + err.message);
        })
        .finally(() => {
          setRegProcessing(false);
        });
    }, 'image/jpeg');
  };

  const handleDeleteStudent = async (student) => {
    const name = typeof student === 'string' ? student : (student.name || 'this student');
    const identifier = typeof student === 'object' ? (student.id || student.roll_number || student.name) : student;

    if (!window.confirm(`Are you sure you want to delete "${name}"?\n\nThis will remove their biometric face data, class enrollments, and attendance history.`)) {
      return;
    }

    try {
      const res = await api.deleteStudent(identifier);
      if (res.status === 'success') {
        // Immediate local state update
        setAllStudentsList(prev => prev.filter(s => {
          const sName = typeof s === 'string' ? s : s.name;
          const sId = typeof s === 'object' ? s.id : s;
          return sName !== name && sId !== identifier;
        }));
        fetchRoster(currentClass);
        fetchDashboard();
        fetchDirectoryStudents(directoryClassFilter);
      } else {
        alert("❌ Error: " + (res.message || "Failed to delete student"));
      }
    } catch (err) {
      alert("❌ Error: " + err.message);
    }
  };

  const handleResetAttendance = async () => {
    if (!window.confirm("Are you sure you want to reset all attendance records for today?\n\n(Registered student accounts will NOT be deleted)")) {
      return;
    }
    try {
      await api.resetDatabase();
      setDashboardData(prev => ({
        ...prev,
        stats: { ...prev.stats, present_today: 0 },
        recent_logs: []
      }));
      fetchDashboard();
      alert("✅ Attendance records reset successfully");
    } catch (err) {
      alert("❌ Error: " + err.message);
    }
  };

  const handleSignOut = () => {
    logoutUser();
    if (onSignOut) onSignOut();
  };

  return (
    <div className="min-h-screen flex overflow-hidden bg-[#f8fafc] text-slate-800 font-sans">
      {/* SIDEBAR */}
      <aside className="w-72 bg-[#0f172a] text-slate-400 p-8 hidden lg:flex flex-col border-r border-slate-800 shrink-0">
        <div className="flex items-center space-x-3 mb-12">
          <div className="w-10 h-10 bg-[#7c3aed] rounded-xl flex items-center justify-center shadow-lg shadow-purple-900/40">
            <Cloud className="text-white w-6 h-6" />
          </div>
          <span className="text-2xl font-black text-white tracking-tighter">EduFlow</span>
        </div>

        <nav className="flex-1 space-y-3">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`sidebar-item flex items-center w-full p-4 rounded-2xl transition-all duration-300 font-black text-xs uppercase tracking-[0.2em] cursor-pointer ${
              activeTab === 'dashboard'
                ? 'bg-white/10 text-white'
                : 'hover:text-slate-300 hover:bg-white/5'
            }`}
          >
            <LayoutDashboard className="mr-4 w-5 h-5" /> Dashboard
          </button>

          <button
            onClick={() => setActiveTab('students')}
            className={`sidebar-item flex items-center w-full p-4 rounded-2xl transition-all duration-300 font-black text-xs uppercase tracking-[0.2em] cursor-pointer ${
              activeTab === 'students'
                ? 'bg-white/10 text-white'
                : 'hover:text-slate-300 hover:bg-white/5'
            }`}
          >
            <Users className="mr-4 w-5 h-5" /> My Students
          </button>

          <button
            onClick={() => setActiveTab('cloud')}
            className={`sidebar-item flex items-center w-full p-4 rounded-2xl transition-all duration-300 font-black text-xs uppercase tracking-[0.2em] cursor-pointer ${
              activeTab === 'cloud'
                ? 'bg-white/10 text-white'
                : 'hover:text-slate-300 hover:bg-white/5'
            }`}
          >
            <FolderOpen className="mr-4 w-5 h-5" /> Note Cloud
          </button>
        </nav>

        <div className="mt-auto pt-8 border-t border-slate-800">
          <button
            onClick={handleSignOut}
            className="flex items-center w-full p-3 hover:text-white transition-colors cursor-pointer text-slate-400"
          >
            <LogOut className="mr-3 w-5 h-5" /> Sign Out
          </button>
        </div>
      </aside>

      {/* MAIN VIEW */}
      <main className="flex-1 overflow-y-auto p-6 md:p-10 lg:p-14 custom-scrollbar">
        {/* HEADER */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-[#0f172a]">Faculty Dashboard</h1>
            <p className="text-slate-500 font-medium mt-1">
              Welcome back, <span className="text-[#7c3aed]">Professor Miller</span>.
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative group">
              <select
                value={currentClass}
                onChange={handleClassChange}
                className="appearance-none bg-white pl-4 pr-10 py-3 rounded-2xl border border-slate-200 font-bold text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-purple-500 cursor-pointer shadow-sm"
              >
                {classesList.map((cls, idx) => (
                  <option key={idx} value={cls}>{cls}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
          </div>
        </header>

        {/* TAB 1: DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="animate-fade-in grid grid-cols-1 xl:grid-cols-3 gap-8">
            <div className="xl:col-span-2 space-y-8">
              {/* Stats Row */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <div className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100">
                  <div className="p-4 rounded-[20px] bg-purple-50 text-purple-600 w-fit mb-6">
                    <Users className="w-5 h-5" />
                  </div>
                  <h3 className="text-slate-400 text-xs font-black uppercase tracking-[0.2em]">Enrolled Students</h3>
                  <p className="text-3xl font-black text-slate-900 mt-2">
                    {rosterData.count !== undefined ? rosterData.count : '--'}
                  </p>
                </div>

                <div className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100">
                  <div className="p-4 rounded-[20px] bg-indigo-50 text-indigo-600 w-fit mb-6">
                    <CheckCircle className="w-5 h-5" />
                  </div>
                  <h3 className="text-slate-400 text-xs font-black uppercase tracking-[0.2em]">Present Today</h3>
                  <p className="text-3xl font-black text-slate-900 mt-2">
                    {dashboardData.stats?.present_today !== undefined ? dashboardData.stats.present_today : '--'}
                  </p>
                </div>

                <div className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100">
                  <div className="p-4 rounded-[20px] bg-blue-50 text-blue-600 w-fit mb-6">
                    <Cloud className="w-5 h-5" />
                  </div>
                  <h3 className="text-slate-400 text-xs font-black uppercase tracking-[0.2em]">Note Storage</h3>
                  <p className="text-3xl font-black text-slate-900 mt-2">12.8 GB</p>
                </div>
              </div>

              {/* Recent Student Progress Table */}
              <section className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100 overflow-hidden">
                <h3 className="text-xl font-black tracking-tight text-slate-800 mb-8">Recent Student Progress</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50/50">
                      <tr className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                        <th className="px-6 py-4">Reg ID</th>
                        <th className="px-6 py-4">Student Name</th>
                        <th className="px-6 py-4">NN Confidence</th>
                        <th className="px-6 py-4">Status</th>
                        <th className="px-6 py-4">Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {dashboardData.recent_logs?.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="px-6 py-6 text-center text-slate-400 text-xs font-bold uppercase">
                            No attendance records today
                          </td>
                        </tr>
                      ) : (
                        dashboardData.recent_logs?.map((row, idx) => {
                          const conf = typeof row[4] === 'number' ? row[4] : parseFloat(row[4]) || 95.0;
                          return (
                            <tr key={idx} className="hover:bg-slate-50 border-b border-slate-100">
                              <td className="px-6 py-4 text-xs font-bold text-slate-400">{row[0] || 'Unknown'}</td>
                              <td className="px-6 py-4 font-black text-slate-800">{row[1]}</td>
                              <td className="px-6 py-4">
                                <span className={`px-2.5 py-1 rounded-full text-[10px] font-black inline-flex items-center gap-1 ${
                                  conf >= 80 
                                    ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' 
                                    : conf >= 60 
                                      ? 'bg-amber-50 text-amber-600 border border-amber-200' 
                                      : 'bg-rose-50 text-rose-600 border border-rose-200'
                                }`}>
                                  ⚡ {conf.toFixed(1)}%
                                </span>
                              </td>
                              <td className="px-6 py-4">
                                <span className="bg-green-100 text-green-600 px-3 py-1 rounded-lg text-[10px] font-black uppercase">
                                  Present
                                </span>
                              </td>
                              <td className="px-6 py-4 text-xs font-bold text-slate-500">{row[2]}</td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>

            {/* Quick Actions Card */}
            <div className="space-y-8">
              <section className="bg-[#0f172a] p-8 rounded-[40px] text-white shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 blur-3xl rounded-full"></div>
                <h3 className="text-lg font-black tracking-[0.1em] uppercase text-purple-300 mb-8 relative z-10">
                  Quick Actions
                </h3>
                <button
                  onClick={startScanner}
                  className="w-full flex items-center p-4 bg-white/5 rounded-2xl border border-white/5 hover:border-white/20 transition-all group cursor-pointer relative z-10 mb-4"
                >
                  <div className="p-3 bg-purple-500/20 text-purple-300 rounded-xl mr-4">
                    <CheckSquare className="w-5 h-5" />
                  </div>
                  <span className="text-sm font-bold text-white">Mark Attendance</span>
                </button>

                <button
                  onClick={() => setActiveTab('cloud')}
                  className="w-full flex items-center p-4 bg-white/5 rounded-2xl border border-white/5 hover:border-white/20 transition-all group relative z-10 cursor-pointer mb-4"
                >
                  <div className="p-3 bg-blue-500/20 text-blue-300 rounded-xl mr-4">
                    <UploadCloud className="w-5 h-5" />
                  </div>
                  <span className="text-sm font-bold">Upload Lecture Notes</span>
                </button>

                <button
                  onClick={handleResetAttendance}
                  className="w-full flex items-center p-4 bg-rose-500/10 rounded-2xl border border-rose-500/20 hover:border-rose-500/40 hover:bg-rose-500/20 transition-all group relative z-10 cursor-pointer text-rose-300"
                >
                  <div className="p-3 bg-rose-500/20 text-rose-300 rounded-xl mr-4">
                    <RotateCcw className="w-5 h-5" />
                  </div>
                  <span className="text-sm font-bold">Reset Today's Attendance</span>
                </button>
              </section>
            </div>
          </div>
        )}

        {/* TAB 2: MY STUDENTS */}
        {activeTab === 'students' && (
          <div className="animate-fade-in">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
              <div>
                <h2 className="text-2xl font-black text-slate-900 tracking-tight">Registered Student Directory</h2>
                <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-1">
                  Total Enrolled: {allStudentsList.length} Students
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                {/* Course Filter Dropdown */}
                <div className="relative">
                  <select
                    value={directoryClassFilter}
                    onChange={(e) => {
                      const val = e.target.value;
                      setDirectoryClassFilter(val);
                      fetchDirectoryStudents(val);
                    }}
                    className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-xs font-black uppercase tracking-wider text-slate-700 focus:outline-none focus:ring-2 focus:ring-purple-500 cursor-pointer shadow-sm pr-8"
                  >
                    <option value="all">All Registered Students</option>
                    {classesList.map((cls, idx) => (
                      <option key={idx} value={cls}>{cls}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>

                <button
                  onClick={() => api.exportCsv()}
                  className="flex items-center px-5 py-2.5 bg-white border border-slate-200 text-slate-600 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-slate-50 transition-all cursor-pointer shadow-sm"
                >
                  <Download className="w-4 h-4 mr-2" /> Export
                </button>
                <button
                  onClick={openRegistrationModal}
                  className="flex items-center px-5 py-2.5 bg-[#7c3aed] text-white rounded-xl text-xs font-black uppercase tracking-widest shadow-lg shadow-purple-900/20 hover:bg-purple-700 transition-all cursor-pointer"
                >
                  <Plus className="w-4 h-4 mr-2" /> Add Student
                </button>
              </div>
            </div>

            <div className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-slate-50/50">
                    <tr className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                      <th className="px-6 py-4">Reg ID</th>
                      <th className="px-6 py-4">Student Name</th>
                      <th className="px-6 py-4">Enrolled Course</th>
                      <th className="px-6 py-4">Biometric Status</th>
                      <th className="px-6 py-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {allStudentsList.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="px-6 py-8 text-center text-slate-400 text-xs font-bold uppercase">
                          No registered students found in this course
                        </td>
                      </tr>
                    ) : (
                      allStudentsList.map((st, idx) => {
                        const name = typeof st === 'string' ? st : (st.name || 'Unknown');
                        const roll = typeof st === 'object' ? (st.roll_number || 'N/A') : 'REG-2025-000';
                        const course = typeof st === 'object' ? (st.class_name || currentClass) : currentClass;
                        return (
                          <tr key={idx} className="hover:bg-slate-50/80 border-b border-slate-100 transition-colors">
                            <td className="px-6 py-4 text-xs font-bold text-slate-400">{roll}</td>
                            <td className="px-6 py-4 font-black text-slate-800">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center font-black text-xs">
                                  {name.substring(0, 2).toUpperCase()}
                                </div>
                                <span>{name}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 text-xs font-bold text-slate-600">{course}</td>
                            <td className="px-6 py-4">
                              <span className="bg-emerald-50 text-emerald-600 border border-emerald-200 px-3 py-1 rounded-full text-[10px] font-black uppercase inline-flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                Active & Verified
                              </span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <button
                                onClick={() => handleDeleteStudent(st)}
                                title={`Delete ${name}`}
                                className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-all cursor-pointer inline-flex items-center gap-1 text-xs font-bold"
                              >
                                <Trash2 className="w-4 h-4" />
                                <span className="hidden sm:inline">Delete</span>
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: NOTE CLOUD */}
        {activeTab === 'cloud' && (
          <div className="animate-fade-in">
            <h2 className="text-3xl font-black text-[#0f172a] mb-6">Digital Note Cloud</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-[32px] border border-slate-100 shadow-sm hover:border-purple-200 transition-all">
                <div className="flex justify-between items-start mb-6">
                  <div className="p-4 bg-purple-50 text-purple-600 rounded-2xl">
                    <FileText className="w-8 h-8" />
                  </div>
                </div>
                <h4 className="text-lg font-black text-slate-800">Lecture 12 - RNNs</h4>
                <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-4">PDF • 2.4 MB</p>
              </div>

              <div className="bg-white p-6 rounded-[32px] border border-slate-100 shadow-sm hover:border-purple-200 transition-all">
                <div className="flex justify-between items-start mb-6">
                  <div className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl">
                    <FileText className="w-8 h-8" />
                  </div>
                </div>
                <h4 className="text-lg font-black text-slate-800">Computer Vision Basics</h4>
                <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-4">PDF • 4.1 MB</p>
              </div>

              <div className="bg-white p-6 rounded-[32px] border border-slate-100 shadow-sm hover:border-purple-200 transition-all">
                <div className="flex justify-between items-start mb-6">
                  <div className="p-4 bg-blue-50 text-blue-600 rounded-2xl">
                    <FileText className="w-8 h-8" />
                  </div>
                </div>
                <h4 className="text-lg font-black text-slate-800">Ethics in AI Guidelines</h4>
                <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-4">DOCX • 1.8 MB</p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* SCANNER MODAL */}
      {isScannerOpen && (
        <div className="fixed inset-0 z-[9999] bg-slate-900/90 backdrop-blur-sm flex justify-center items-center">
          <div className="bg-[#1e293b] p-8 rounded-[32px] border border-slate-700 shadow-2xl w-[500px] text-center">
            <h2 className="text-2xl font-black text-white mb-2">Scanning Class</h2>
            <p className="text-purple-400 font-bold text-xs uppercase tracking-widest mb-6">
              Class: {currentClass}
            </p>
            <div className="relative rounded-2xl overflow-hidden border-2 border-purple-500 shadow-[0_0_30px_rgba(168,85,247,0.4)]">
              <video
                ref={scannerVideoRef}
                width="440"
                height="330"
                autoPlay
                playsInline
                muted
                className="w-full bg-black scale-x-[-1]"
              />
              <div
                className="absolute top-0 left-0 w-full h-1 bg-green-400 shadow-[0_0_15px_#4ade80]"
                style={{ animation: 'scanLine 2s infinite linear' }}
              />
            </div>
            <p className="mt-6 font-mono text-sm font-bold text-slate-400">
              {scanStatusHtml ? scanStatusHtml : scanStatusText}
            </p>
            <button
              onClick={stopScanner}
              className="mt-6 px-8 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl font-bold transition-all text-xs uppercase tracking-widest cursor-pointer"
            >
              Close Scanner
            </button>
          </div>
        </div>
      )}

      {/* REGISTRATION MODAL */}
      {isRegModalOpen && (
        <div className="fixed inset-0 z-[9999] bg-slate-900/95 backdrop-blur-sm flex justify-center items-center">
          <div className="bg-white p-8 rounded-[32px] shadow-2xl w-[450px] text-center relative text-slate-900">
            <h2 className="text-2xl font-black text-slate-900 mb-6">New Student</h2>

            <div className="space-y-4">
              <div className="text-left">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">
                  Student Name
                </label>
                <input
                  type="text"
                  value={newStudentName}
                  onChange={(e) => setNewStudentName(e.target.value)}
                  placeholder="Enter Full Name"
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl font-bold focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div className="text-left">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">
                  Assign to Class
                </label>
                <div className="relative">
                  <select
                    value={newStudentClass}
                    onChange={(e) => setNewStudentClass(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold appearance-none focus:outline-none focus:ring-2 focus:ring-purple-500 text-slate-700 cursor-pointer"
                  >
                    {classesList.map((cls, idx) => (
                      <option key={idx} value={cls}>{cls}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>

              <div className="relative rounded-2xl overflow-hidden bg-black aspect-video border-2 border-slate-100 shadow-inner">
                <video
                  ref={regVideoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover scale-x-[-1]"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-6">
              <button
                onClick={closeRegModal}
                className="py-3 bg-slate-100 text-slate-500 rounded-xl font-black text-xs uppercase tracking-widest hover:bg-slate-200 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={registerStudent}
                disabled={regProcessing}
                className="py-3 bg-[#7c3aed] text-white rounded-xl font-black text-xs uppercase tracking-widest hover:bg-purple-700 transition-colors shadow-lg shadow-purple-900/20 cursor-pointer"
              >
                {regProcessing ? "Processing..." : "Capture & Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
