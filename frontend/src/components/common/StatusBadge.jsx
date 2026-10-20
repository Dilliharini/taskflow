import React, { useState, useEffect } from 'react';
import { getSystemHealth } from '../../api/health';
import { Activity, Database, CheckCircle2, AlertTriangle, XCircle, RefreshCw } from 'lucide-react';

export default function StatusBadge() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSystemHealth(false);
      setHealth(data);
    } catch (err) {
      setError(err.message || 'Unable to reach backend');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    // Auto-refresh every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-3 bg-slate-800/80 backdrop-blur border border-slate-700/60 rounded-xl px-4 py-2 text-xs shadow-sm">
      {/* Backend API status */}
      <div className="flex items-center gap-1.5">
        <Activity className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-slate-400">API:</span>
        {loading && !health ? (
          <span className="text-amber-400 animate-pulse font-medium">Checking...</span>
        ) : error ? (
          <span className="flex items-center gap-1 text-rose-400 font-medium">
            <XCircle className="w-3 h-3" /> Offline
          </span>
        ) : (
          <span className="flex items-center gap-1 text-emerald-400 font-medium">
            <CheckCircle2 className="w-3 h-3" /> Online
          </span>
        )}
      </div>

      <div className="h-3 w-px bg-slate-700" />

      {/* Database status */}
      <div className="flex items-center gap-1.5">
        <Database className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-slate-400">PostgreSQL:</span>
        {loading && !health ? (
          <span className="text-amber-400 animate-pulse font-medium">Probing...</span>
        ) : health?.database?.status === 'connected' ? (
          <span className="flex items-center gap-1 text-emerald-400 font-medium">
            <CheckCircle2 className="w-3 h-3" />
            Connected {health.database.latency_ms ? `(${health.database.latency_ms}ms)` : ''}
          </span>
        ) : health?.database?.status === 'disconnected' ? (
          <span className="flex items-center gap-1 text-amber-400 font-medium" title={health.database.error}>
            <AlertTriangle className="w-3 h-3" /> Standby
          </span>
        ) : (
          <span className="flex items-center gap-1 text-slate-400">--</span>
        )}
      </div>

      {/* Manual refresh button */}
      <button
        type="button"
        onClick={checkHealth}
        disabled={loading}
        title="Refresh health checks"
        className="p-1 hover:bg-slate-700 rounded-md transition text-slate-400 hover:text-slate-200 disabled:opacity-50 cursor-pointer ml-1"
      >
        <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
      </button>
    </div>
  );
}
