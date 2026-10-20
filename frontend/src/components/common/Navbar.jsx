import React from 'react';
import StatusBadge from './StatusBadge';
import { Layers, Kanban, CheckSquare } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }
  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-sky-400 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <Layers className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-white tracking-tight">TaskFlow</span>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full">
                Phase 3
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Collaborative Project Management</p>
          </div>
        </div>

        {/* Center Navigation Links (Preview for future phases) */}
        <nav className="hidden md:flex items-center gap-1 text-sm font-medium text-slate-400">
          <span className="flex items-center gap-1.5 px-3 py-1.5 text-white bg-slate-800/80 rounded-lg">
            <Kanban className="w-4 h-4 text-indigo-400" /> System Overview
          </span>
          <span className="flex items-center gap-1.5 px-3 py-1.5 hover:text-slate-200 transition opacity-60 cursor-not-allowed">
            <CheckSquare className="w-4 h-4" /> Projects (Phase 4)
          </span>
          {user && <span className="px-3 py-1.5 text-slate-300">{user.name}</span>}
        </nav>

        {/* Right Status Badge */}
        <div className="flex items-center gap-3">
          <StatusBadge />
          {user ? <button type="button" onClick={handleLogout} className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 transition hover:bg-slate-800">Sign out</button> : <Link to="/login" className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 transition hover:bg-slate-800">Sign in</Link>}
        </div>
      </div>
    </header>
  );
}
