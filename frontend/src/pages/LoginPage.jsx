import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

const inputClass = 'w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-slate-100 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20';

export default function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await login({ email, password });
      navigate(location.state?.from?.pathname || '/', { replace: true });
    } catch (err) {
      setError(err.message || 'Unable to sign in. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-[75vh] max-w-md items-center px-4 py-12">
      <section className="w-full rounded-3xl border border-slate-700/70 bg-slate-800/60 p-8 shadow-2xl">
        <p className="text-sm font-semibold uppercase tracking-widest text-indigo-400">Welcome back</p>
        <h1 className="mt-2 text-3xl font-bold text-white">Sign in to TaskFlow</h1>
        <p className="mt-2 text-sm text-slate-400">Continue to your collaborative workspace.</p>
        {location.state?.message && <p className="mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-300" role="status">{location.state.message}</p>}
        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <label className="block space-y-2 text-sm font-medium text-slate-200">Email
            <input className={inputClass} type="email" autoComplete="email" required maxLength={320} value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="block space-y-2 text-sm font-medium text-slate-200">Password
            <input className={inputClass} type="password" autoComplete="current-password" required maxLength={128} value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300" role="alert">{error}</p>}
          <button className="w-full rounded-xl bg-indigo-600 px-4 py-3 font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-wait disabled:opacity-60" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-400">New to TaskFlow? <Link className="font-semibold text-indigo-400 hover:text-indigo-300" to="/register">Create an account</Link></p>
      </section>
    </main>
  );
}