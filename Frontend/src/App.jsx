import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LandingPage from './pages/LandingPage';
import TeacherDashboard from './pages/TeacherDashboard';
import StudentDashboard from './pages/StudentDashboard';

function AppContent() {
  const { user } = useAuth();
  const [activePortal, setActivePortal] = useState(() => {
    return user ? user.role : null;
  });

  const handleLoginSuccess = (role) => {
    setActivePortal(role);
  };

  const handleSignOut = () => {
    setActivePortal(null);
  };

  if (user && (activePortal === 'teacher' || user.role === 'teacher')) {
    return <TeacherDashboard onSignOut={handleSignOut} />;
  }

  if (user && (activePortal === 'student' || user.role === 'student')) {
    return <StudentDashboard onSignOut={handleSignOut} />;
  }

  return <LandingPage onLoginSuccess={handleLoginSuccess} />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
