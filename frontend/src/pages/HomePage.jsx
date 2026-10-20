import React, { useState, useEffect } from 'react';
import { getSystemHealth } from '../api/health';
import { 
  Server, Database, Code, CheckCircle, Clock, Terminal, 
  ExternalLink, Shield, Cpu, RefreshCw, AlertCircle, ArrowRight
} from 'lucide-react';

export default function HomePage() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSystemHealth(false);
      setHealthData(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to backend service');
      setHealthData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const phases = [
    { num: 1, title: 'Project Structure & Foundation', status: 'completed', desc: 'React + Vite, FastAPI, PostgreSQL configuration, health checks, tests' },
    { num: 2, title: 'Database Models & Migrations', status: 'next', desc: 'SQLAlchemy 2.x models, Alembic migrations, DB integration tests' },
    { num: 3, title: 'Authentication & Security', status: 'pending', desc: 'Argon2 hashing, JWT lifecycle, protected routes, security tests' },
    { num: 4, title: 'Projects & Roles', status: 'pending', desc: 'CRUD, team memberships, role-based authorization' },
    { num: 5, title: 'Tasks & Boards', status: 'pending', desc: 'Kanban boards, task assignments, priorities, deadlines, search' },
    { num: 6, title: 'Collaboration & Comments', status: 'pending', desc: 'Comments, activity logs, audit history' },
    { num: 7, title: 'Notifications & WebSockets', status: 'pending', desc: 'Real-time board updates and notification bell' },
    { num: 8, title: 'Dashboard & Polish', status: 'pending', desc: 'Aggregated summaries, accessibility, responsive polish' },
    { num: 9, title: 'Testing & Hardening', status: 'pending', desc: 'End-to-end integration, security audits, performance profiling' },
    { num: 10, title: 'Production Deployment', status: 'pending', desc: 'GitHub CI/CD, production builds, deployment docs' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-slate-800/80 to-slate-900 border border-slate-700/60 p-8 sm:p-12 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Phase 1 Foundation Live
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Collaborative Project Management, Built for High Velocity.
          </h1>
          <p className="text-base sm:text-lg text-slate-300 leading-relaxed">
            TaskFlow combines the visual agility of Trello boards with the structured power of Asana. 
            Engineered with FastAPI, SQLAlchemy 2.x, PostgreSQL, and React.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <a
              href="http://localhost:8000/api/v1/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition shadow-lg shadow-indigo-600/25"
            >
              Explore Interactive Swagger Docs
              <ExternalLink className="w-4 h-4" />
            </a>
            <button
              type="button"
              onClick={fetchHealth}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium text-sm transition cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
              Re-probe System Health
            </button>
          </div>
        </div>
      </div>

      {/* Diagnostics & Live Status Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Backend API Card */}
        <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 backdrop-blur space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Server className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white">FastAPI Backend</h3>
                <p className="text-xs text-slate-400">REST API & WebSockets</p>
              </div>
            </div>
            {loading ? (
              <span className="text-xs text-amber-400 animate-pulse">Checking</span>
            ) : error ? (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">Offline</span>
            ) : (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Healthy</span>
            )}
          </div>

          <div className="space-y-2 text-xs border-t border-slate-700/60 pt-4 text-slate-300">
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Framework</span>
              <span className="font-mono text-slate-200">FastAPI + Uvicorn</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Environment</span>
              <span className="font-mono text-slate-200">{healthData?.environment || 'development'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Base URL</span>
              <span className="font-mono text-slate-200">http://localhost:8000</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">API Prefix</span>
              <span className="font-mono text-slate-200">/api/v1</span>
            </div>
          </div>
        </div>

        {/* PostgreSQL Database Card */}
        <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 backdrop-blur space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white">PostgreSQL</h3>
                <p className="text-xs text-slate-400">SQLAlchemy 2.x + psycopg 3</p>
              </div>
            </div>
            {loading ? (
              <span className="text-xs text-amber-400 animate-pulse">Probing</span>
            ) : healthData?.database?.status === 'connected' ? (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Connected</span>
            ) : (
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">Standby</span>
            )}
          </div>

          <div className="space-y-2 text-xs border-t border-slate-700/60 pt-4 text-slate-300">
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Driver</span>
              <span className="font-mono text-slate-200">{healthData?.database?.driver || 'psycopg (v3)'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Latency</span>
              <span className="font-mono text-slate-200">
                {healthData?.database?.latency_ms ? `${healthData.database.latency_ms} ms` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Target DB</span>
              <span className="font-mono text-slate-200">localhost:5432/taskflow</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Docker Service</span>
              <span className="font-mono text-indigo-400">docker compose up -d</span>
            </div>
          </div>
        </div>

        {/* Security & Client Card */}
        <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 backdrop-blur space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Client & Security</h3>
                <p className="text-xs text-slate-400">CORS, Axios & Vite</p>
              </div>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Active</span>
          </div>

          <div className="space-y-2 text-xs border-t border-slate-700/60 pt-4 text-slate-300">
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Frontend Port</span>
              <span className="font-mono text-slate-200">http://localhost:5173</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Vite Proxy</span>
              <span className="font-mono text-slate-200">/api/v1 -&gt; :8000</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">CORS Allowed</span>
              <span className="font-mono text-slate-200">5173, 3000</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Credentials</span>
              <span className="font-mono text-slate-200">withCredentials: true</span>
            </div>
          </div>
        </div>
      </div>

      {/* Development Roadmap */}
      <div className="bg-slate-800/40 border border-slate-700/60 rounded-3xl p-6 sm:p-8 space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Application Development Roadmap</h2>
          <p className="text-sm text-slate-400 mt-1">
            TaskFlow is architected and built sequentially in 10 verified engineering phases.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {phases.map((phase) => (
            <div 
              key={phase.num}
              className={`p-4 rounded-2xl border transition ${
                phase.status === 'completed'
                  ? 'bg-slate-800/80 border-emerald-500/40 shadow-sm'
                  : phase.status === 'next'
                  ? 'bg-indigo-950/30 border-indigo-500/50'
                  : 'bg-slate-900/40 border-slate-800/60 opacity-60'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <span className={`w-6 h-6 rounded-lg text-xs font-bold flex items-center justify-center ${
                    phase.status === 'completed'
                      ? 'bg-emerald-500 text-slate-950'
                      : phase.status === 'next'
                      ? 'bg-indigo-500 text-white'
                      : 'bg-slate-800 text-slate-400'
                  }`}>
                    {phase.num}
                  </span>
                  <h3 className="font-semibold text-sm text-white">{phase.title}</h3>
                </div>
                {phase.status === 'completed' && (
                  <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    <CheckCircle className="w-3 h-3" /> Ready
                  </span>
                )}
                {phase.status === 'next' && (
                  <span className="flex items-center gap-1 text-[11px] font-semibold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20">
                    Next Phase
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-2 pl-8">{phase.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Developer Quickstart Commands */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4">
        <div className="flex items-center gap-2 text-indigo-400">
          <Terminal className="w-5 h-5" />
          <h2 className="text-lg font-bold text-white">Developer Run Commands</h2>
        </div>
        <p className="text-xs text-slate-400">
          Run these verified commands in separate terminal sessions from <code className="text-slate-300 font-mono">D:\taskflow</code>:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 space-y-2">
            <span className="text-xs font-semibold text-indigo-400">1. Backend API (FastAPI)</span>
            <pre className="text-xs font-mono text-slate-300 bg-slate-900 p-2.5 rounded-lg overflow-x-auto">
              $env:PYTHONPATH="backend"<br />
              .\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
            </pre>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 space-y-2">
            <span className="text-xs font-semibold text-sky-400">2. Frontend Dev (Vite + React)</span>
            <pre className="text-xs font-mono text-slate-300 bg-slate-900 p-2.5 rounded-lg overflow-x-auto">
              cd frontend<br />
              npm run dev
            </pre>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 space-y-2">
            <span className="text-xs font-semibold text-emerald-400">3. Backend Tests (pytest)</span>
            <pre className="text-xs font-mono text-slate-300 bg-slate-900 p-2.5 rounded-lg overflow-x-auto">
              cd backend<br />
              ..\.venv\Scripts\pytest.exe
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
