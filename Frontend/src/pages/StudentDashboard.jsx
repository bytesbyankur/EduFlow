import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Cloud, 
  BarChart2, 
  Calendar, 
  BookOpen, 
  Folder, 
  LogOut, 
  Search, 
  CheckCircle, 
  TrendingUp, 
  Book, 
  Award, 
  Calculator, 
  FileText 
} from 'lucide-react';
import api from '../services/api';

export default function StudentDashboard({ onSignOut }) {
  const { user, logoutUser } = useAuth();
  const loggedInStudent = user?.name || localStorage.getItem('currentUser') || 'Taylor Swift';

  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'attendance', 'courses', 'cloud'
  const [studentData, setStudentData] = useState({
    name: loggedInStudent,
    attendance_rate: 0,
    present_days: 0,
    total_days: 30,
    gpa: 3.8,
    credits: 20,
    rank: '#1',
    courses: [],
    graph_data: [0, 0, 0, 0, 0, 0, 0]
  });
  const [historyLogs, setHistoryLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch Student Data
  const fetchStudentData = useCallback(async () => {
    try {
      const data = await api.getStudentStats(loggedInStudent);
      setStudentData(data);
    } catch (err) {
      console.error("Error fetching student data:", err);
    }
  }, [loggedInStudent]);

  // Fetch Student History
  const fetchHistory = useCallback(async () => {
    try {
      const data = await api.getStudentHistory(loggedInStudent);
      setHistoryLogs(data.history || []);
    } catch (err) {
      console.error("Error fetching history:", err);
    }
  }, [loggedInStudent]);

  useEffect(() => {
    fetchStudentData();
    fetchHistory();
  }, [fetchStudentData, fetchHistory]);

  const handleSignOut = () => {
    logoutUser();
    if (onSignOut) onSignOut();
  };

  // Generate SVG coordinates for Attendance Graph
  const generateGraphCoords = () => {
    const dataPoints = studentData.graph_data && studentData.graph_data.length > 0 
      ? studentData.graph_data 
      : [0, 0, 0, 0, 0, 0, 0];
    const maxVal = Math.max(...dataPoints, 3);

    return dataPoints.map((val, index) => {
      const x = (index / (dataPoints.length - 1)) * 100;
      const y = 50 - ((val / maxVal) * 40);
      return { x, y, val };
    });
  };

  const graphPoints = generateGraphCoords();
  const polylineStr = graphPoints.map(p => `${p.x},${p.y}`).join(" ");

  // Target Check logic
  const TARGET = Math.ceil((studentData.total_days || 30) * 0.75); // ~23
  const isSafe = (studentData.present_days || 0) >= TARGET;
  const needed = Math.max(0, TARGET - (studentData.present_days || 0));
  const progressPercent = Math.min(((studentData.present_days || 0) / TARGET) * 100, 100);

  // Get Initials for Avatar
  const getInitials = (name) => {
    if (!name) return 'ST';
    const parts = name.split(' ');
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <div className="min-h-screen flex overflow-hidden bg-[#f8fafc] text-slate-800 font-sans">
      {/* SIDEBAR */}
      <aside className="w-72 bg-[#0f172a] text-slate-400 p-8 hidden lg:flex flex-col shrink-0 border-r border-slate-800">
        <div className="flex items-center space-x-3 mb-12">
          <div className="w-10 h-10 bg-[#7c3aed] rounded-xl flex items-center justify-center shadow-lg shadow-purple-900/40">
            <Cloud className="text-white w-6 h-6" />
          </div>
          <span className="text-2xl font-black text-white tracking-tighter">EduFlow</span>
        </div>

        <nav className="space-y-3 flex-1">
          <button
            onClick={() => setActiveTab('overview')}
            id="btn-overview"
            className={`sidebar-btn flex items-center w-full p-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] transition-all cursor-pointer ${
              activeTab === 'overview'
                ? 'bg-[#7c3aed] text-white shadow-lg shadow-purple-900/20 hover:scale-[1.02]'
                : 'hover:bg-white/5 text-slate-400 hover:text-white'
            }`}
          >
            <BarChart2 className="mr-4 w-5 h-5" /> Overview
          </button>

          <button
            onClick={() => setActiveTab('attendance')}
            id="btn-attendance"
            className={`sidebar-btn flex items-center w-full p-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] transition-all cursor-pointer ${
              activeTab === 'attendance'
                ? 'bg-[#7c3aed] text-white shadow-lg shadow-purple-900/20 hover:scale-[1.02]'
                : 'hover:bg-white/5 text-slate-400 hover:text-white'
            }`}
          >
            <Calendar className="mr-4 w-5 h-5" /> Attendance
          </button>

          <button
            onClick={() => setActiveTab('courses')}
            className={`sidebar-btn flex items-center w-full p-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] transition-all cursor-pointer ${
              activeTab === 'courses'
                ? 'bg-[#7c3aed] text-white shadow-lg shadow-purple-900/20 hover:scale-[1.02]'
                : 'hover:bg-white/5 text-slate-400 hover:text-white'
            }`}
          >
            <BookOpen className="mr-4 w-5 h-5" /> Courses
          </button>

          <button
            onClick={() => setActiveTab('cloud')}
            className={`sidebar-btn flex items-center w-full p-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] transition-all cursor-pointer ${
              activeTab === 'cloud'
                ? 'bg-[#7c3aed] text-white shadow-lg shadow-purple-900/20 hover:scale-[1.02]'
                : 'hover:bg-white/5 text-slate-400 hover:text-white'
            }`}
          >
            <Folder className="mr-4 w-5 h-5" /> Note Cloud
          </button>
        </nav>

        {/* Cloud Usage */}
        <div className="mt-auto bg-[#1e293b] p-6 rounded-3xl border border-slate-700 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-20 h-20 bg-purple-500/20 blur-2xl rounded-full -mr-5 -mt-5"></div>
          <div className="flex justify-between items-center mb-2 relative z-10">
            <h4 className="text-white text-[10px] font-black uppercase tracking-widest">Cloud Usage</h4>
            <Cloud className="w-3 h-3 text-purple-400" />
          </div>
          <div className="w-full h-1.5 bg-slate-700 rounded-full overflow-hidden mb-3 relative z-10">
            <div className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 w-[42%]"></div>
          </div>
          <p className="text-[10px] text-slate-500 font-bold relative z-10">2.1 GB of 5 GB used</p>
        </div>

        <button
          onClick={handleSignOut}
          className="mt-6 flex items-center w-full p-2 hover:text-white transition-colors text-xs font-bold uppercase tracking-widest text-slate-500 cursor-pointer"
        >
          <LogOut className="mr-3 w-4 h-4" /> Sign Out
        </button>
      </aside>

      {/* MAIN VIEW */}
      <main className="flex-1 overflow-y-auto p-6 md:p-10 lg:p-14 custom-scrollbar">
        {/* HEADER */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6 animate-fade-in">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-[#0f172a]">
              Hello, <span id="student-name" className="text-[#7c3aed]">{studentData.name.split(" ")[0]}</span>!
            </h1>
            <p className="text-slate-500 font-medium mt-1">
              Here is what's happening in your <span className="text-purple-600 font-bold">Semester 4</span>.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative hidden sm:block">
              <input
                type="text"
                placeholder="Search notes..."
                className="pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-2xl text-sm font-bold w-64 focus:outline-none focus:ring-4 focus:ring-purple-100 transition-all shadow-sm"
              />
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            </div>
            <div className="w-12 h-12 bg-[#d8b4fe] rounded-2xl flex items-center justify-center text-[#7c3aed] font-black shadow-inner">
              {getInitials(studentData.name)}
            </div>
          </div>
        </header>

        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div id="view-overview" className="animate-fade-in">
            {/* Stat Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <div className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100 relative overflow-hidden group hover:shadow-lg transition-all duration-300">
                <div className="absolute top-0 right-0 w-32 h-32 bg-purple-50 rounded-full -mr-10 -mt-10 transition-transform group-hover:scale-110 duration-500"></div>
                <div className="p-4 rounded-[20px] bg-purple-50 text-purple-600 w-fit mb-6 relative z-10">
                  <CheckCircle className="w-5 h-5" />
                </div>
                <h3 className="text-slate-400 text-xs font-black uppercase tracking-[0.2em] relative z-10">Attendance</h3>
                <div className="flex items-end gap-2 mt-2 relative z-10">
                  <p id="overall-attendance" className="text-4xl font-black text-slate-900">
                    {studentData.attendance_rate}%
                  </p>
                </div>
              </div>

              <div className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100 group hover:shadow-lg transition-all duration-300">
                <div className="p-4 rounded-[20px] bg-indigo-50 text-indigo-600 w-fit mb-6">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <h3 className="text-slate-400 text-xs font-black uppercase tracking-[0.2em]">GPA</h3>
                <p id="student-gpa" className="text-4xl font-black text-slate-900 mt-2">
                  {studentData.gpa}
                </p>
              </div>

              <div className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100 group hover:shadow-lg transition-all duration-300">
                <div className="p-4 rounded-[20px] bg-blue-50 text-blue-600 w-fit mb-6">
                  <Book className="w-5 h-5" />
                </div>
                <h3 className="text-slate-400 text-xs font-black uppercase tracking-[0.2em]">Credits</h3>
                <p id="student-credits" className="text-4xl font-black text-slate-900 mt-2">
                  {studentData.credits}
                </p>
              </div>

              <div className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100 group hover:shadow-lg transition-all duration-300">
                <div className="p-4 rounded-[20px] bg-orange-50 text-orange-600 w-fit mb-6">
                  <Award className="w-5 h-5" />
                </div>
                <h3 className="text-slate-400 text-xs font-black uppercase tracking-[0.2em]">Class Rank</h3>
                <p id="student-rank" className="text-4xl font-black text-slate-900 mt-2">
                  {studentData.rank}
                </p>
              </div>
            </div>

            {/* Academic Progress */}
            <div className="bg-white p-10 rounded-[40px] shadow-sm border border-slate-100">
              <div className="flex justify-between items-center mb-8">
                <h3 className="text-xl font-black tracking-tight text-slate-800">Academic Progress</h3>
                <button 
                  onClick={() => setActiveTab('attendance')}
                  className="text-xs font-black text-[#7c3aed] uppercase tracking-widest bg-purple-50 px-4 py-2 rounded-xl hover:bg-purple-100 transition-all cursor-pointer"
                >
                  Detailed View
                </button>
              </div>

              <div id="course-list" className="space-y-4">
                {studentData.courses?.length === 0 ? (
                  <p className="text-center text-slate-400 text-xs font-bold uppercase py-6">
                    No course records registered
                  </p>
                ) : (
                  studentData.courses?.map((course, idx) => {
                    let statusColor = "text-green-600 bg-green-50";
                    let iconColor = "text-[#7c3aed]";

                    if (course.status === "At Risk") {
                      statusColor = "text-orange-600 bg-orange-50";
                      iconColor = "text-orange-500";
                    } else if (course.status === "Critical") {
                      statusColor = "text-red-600 bg-red-50";
                      iconColor = "text-red-500";
                    }

                    return (
                      <div
                        key={idx}
                        className="flex items-center p-4 rounded-2xl bg-slate-50 border border-slate-100 mb-3 hover:bg-white hover:shadow-md transition-all"
                      >
                        <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center shadow-sm mr-4">
                          <Book className={`w-6 h-6 ${iconColor}`} />
                        </div>
                        <div className="flex-1">
                          <h4 className="text-sm font-black text-slate-800">{course.name}</h4>
                          <div className="flex items-center mt-1">
                            <span className={`text-[10px] font-bold ${statusColor} px-2 py-0.5 rounded-md uppercase tracking-widest mr-2`}>
                              {course.status}
                            </span>
                            <span className="text-xs text-slate-400 font-bold">
                              {course.present} / 10 Sessions
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Attendance</p>
                          <p className="text-xl font-black text-slate-900">{course.rate}%</p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: ATTENDANCE */}
        {activeTab === 'attendance' && (
          <div id="view-attendance" className="animate-fade-in">
            <h2 className="text-3xl font-black text-[#0f172a] mb-8">Attendance Analytics</h2>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
              {/* Trends Graph */}
              <div className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100 flex flex-col h-[450px]">
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <h3 className="text-xl font-black tracking-tight text-slate-900">Attendance Trends</h3>
                    <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-1">Last 7 Days</p>
                  </div>
                  <div className="flex gap-2 items-center">
                    <span className="w-3 h-3 rounded-full bg-[#7c3aed]"></span>
                    <span className="text-[10px] font-bold text-slate-500 uppercase">Your Activity</span>
                  </div>
                </div>
                <div className="flex-1 w-full relative bg-slate-50 rounded-3xl overflow-hidden border border-slate-100">
                  <svg
                    id="attendance-graph"
                    className="absolute inset-0 w-full h-full p-6"
                    viewBox="0 0 100 50"
                    preserveAspectRatio="none"
                  >
                    {polylineStr && (
                      <polyline
                        points={polylineStr}
                        fill="none"
                        stroke="#7c3aed"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        style={{ filter: "drop-shadow(0px 4px 4px rgba(124, 58, 237, 0.3))" }}
                      />
                    )}
                    {graphPoints.map((pt, i) => (
                      <circle
                        key={i}
                        cx={pt.x}
                        cy={pt.y}
                        r="2.5"
                        fill="white"
                        stroke="#7c3aed"
                        strokeWidth="2"
                      >
                        <title>{pt.val} Classes</title>
                      </circle>
                    ))}
                  </svg>
                </div>
              </div>

              {/* 75% Calculator Card */}
              <div
                id="attendance-calc-card"
                className={`p-10 rounded-[40px] text-white shadow-xl shadow-slate-900/20 relative overflow-hidden transition-all duration-500 flex flex-col justify-center h-[450px] ${
                  isSafe ? 'bg-green-600' : 'bg-[#0f172a]'
                }`}
              >
                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl -mr-16 -mt-16"></div>
                <div className="relative z-10">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 bg-white/10 rounded-xl">
                      <Calculator className="w-6 h-6 text-purple-300" />
                    </div>
                    <h3 className="text-sm font-black tracking-[0.2em] uppercase text-white">75% Target Check</h3>
                  </div>
                  <h2 id="calc-status" className="text-4xl font-black mb-4">
                    {isSafe ? "You are Safe! 🎉" : `Attend ${needed} More`}
                  </h2>
                  <p id="calc-message" className="text-base text-slate-300 font-medium leading-relaxed mb-8">
                    {isSafe 
                      ? `Great job! You have attended ${studentData.present_days} classes. You are above the 75% threshold.`
                      : `To reach 75% eligibility, you must attend ${needed} more classes out of the remaining sessions.`}
                  </p>
                  <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      id="calc-progress-bar"
                      className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-1000"
                      style={{ width: `${progressPercent}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest mt-3">
                    <span className="text-slate-300">Current: {studentData.present_days} classes</span>
                    <span className="text-purple-200">Target ({TARGET} Classes)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* History Log Card */}
            <div className="bg-white p-8 rounded-[40px] shadow-sm border border-slate-100 flex flex-col h-[400px]">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-black text-slate-900">Full History Log</h3>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  {historyLogs.length} Records
                </span>
              </div>

              <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 relative">
                <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-white to-transparent pointer-events-none sticky"></div>
                <div id="history-list" className="space-y-3">
                  {historyLogs.length === 0 ? (
                    <p className="text-center text-slate-400 text-xs font-bold mt-10 uppercase">
                      No records found.
                    </p>
                  ) : (
                    historyLogs.map((log, idx) => {
                      const dateObj = new Date(log.date);
                      const month = !isNaN(dateObj.getTime())
                        ? dateObj.toLocaleString('default', { month: 'short' }).toUpperCase()
                        : 'LOG';
                      const day = !isNaN(dateObj.getTime())
                        ? String(dateObj.getDate()).padStart(2, '0')
                        : '01';

                      return (
                        <div
                          key={idx}
                          className="flex items-center p-3 rounded-2xl bg-slate-50 border border-slate-100"
                        >
                          <div className="flex-shrink-0 w-12 text-center mr-4">
                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{month}</p>
                            <p className="text-xl font-black text-slate-800 leading-none">{day}</p>
                          </div>
                          <div className="flex-1 border-l border-slate-200 pl-4">
                            <h4 className="text-xs font-black text-slate-700">{log.class}</h4>
                            <p className="text-[10px] font-bold text-slate-400 mt-0.5">
                              Checked in at <span className="text-purple-600 font-bold">{log.time}</span>
                            </p>
                          </div>
                          <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: COURSES */}
        {activeTab === 'courses' && (
          <div className="animate-fade-in">
            <h2 className="text-3xl font-black text-[#0f172a] mb-6">Registered Courses</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {studentData.courses?.map((c, idx) => (
                <div key={idx} className="bg-white p-8 rounded-[32px] border border-slate-100 shadow-sm">
                  <div className="p-4 bg-purple-50 text-purple-600 rounded-2xl w-fit mb-4">
                    <BookOpen className="w-6 h-6" />
                  </div>
                  <h4 className="text-lg font-black text-slate-800">{c.name}</h4>
                  <p className="text-xs text-slate-500 font-bold mt-1">10 Scheduled Sessions</p>
                  <div className="mt-6 flex justify-between items-center">
                    <span className="text-xs font-black text-purple-600 bg-purple-50 px-3 py-1 rounded-lg">
                      {c.present} Attended
                    </span>
                    <span className="text-lg font-black text-slate-900">{c.rate}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: NOTE CLOUD */}
        {activeTab === 'cloud' && (
          <div className="animate-fade-in">
            <h2 className="text-3xl font-black text-[#0f172a] mb-6">Student Cloud Repository</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-[32px] border border-slate-100 shadow-sm">
                <div className="p-4 bg-purple-50 text-purple-600 rounded-2xl w-fit mb-4">
                  <FileText className="w-8 h-8" />
                </div>
                <h4 className="text-lg font-black text-slate-800">Lecture 12 - RNNs</h4>
                <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-4">PDF • 2.4 MB</p>
              </div>
              <div className="bg-white p-6 rounded-[32px] border border-slate-100 shadow-sm">
                <div className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl w-fit mb-4">
                  <FileText className="w-8 h-8" />
                </div>
                <h4 className="text-lg font-black text-slate-800">Computer Vision 101</h4>
                <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mb-4">PDF • 4.1 MB</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
