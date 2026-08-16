import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('eduflow_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const [role, setRole] = useState(() => {
    const savedRole = localStorage.getItem('eduflow_role');
    return savedRole || 'teacher';
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('eduflow_user', JSON.stringify(user));
      localStorage.setItem('currentUser', user.name || '');
      localStorage.setItem('eduflow_role', user.role || 'teacher');
    } else {
      localStorage.removeItem('eduflow_user');
      localStorage.removeItem('currentUser');
      localStorage.removeItem('eduflow_role');
    }
  }, [user]);

  const loginUser = (userData) => {
    setUser(userData);
    setRole(userData.role);
  };

  const logoutUser = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, role, setRole, loginUser, logoutUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
