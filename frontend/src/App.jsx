import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/common/Navbar';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProtectedRoute from './components/common/ProtectedRoute';
import { AuthProvider, useAuth } from './auth/AuthContext';
import ProjectDetailPage from './pages/ProjectDetailPage';

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <ApplicationFrame />
      </AuthProvider>
    </Router>
  );
}

function ApplicationFrame() {
  const { user } = useAuth();

  return (
    <>
      <Navbar />
      <div className={`flex min-h-screen flex-col ${user ? 'lg:pl-[260px]' : ''}`}>
        <main className="flex-1">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-700/70 px-4 py-5 text-center text-xs text-slate-500 sm:px-6">
          <p>TaskFlow <span aria-hidden="true">·</span> Make meaningful work move forward.</p>
        </footer>
      </div>
    </>
  );
}
