import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

const inputClass = 'focus-ring w-full rounded-xl border border-slate-700 bg-white px-4 py-3 text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-indigo-400';

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
    <main className="mx-auto flex min-h-[calc(100vh-11rem)] max-w-md items-center px-4 py-12">
      <section className="surface-shadow w-full rounded-3xl border border-slate-700 bg-white p-7 sm:p-9">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-400">Welcome back</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">Sign in to TaskFlow</h1>
        <p className="mt-2 text-sm text-slate-400">Pick up where your team left off.</p>
        {location.state?.message && <p className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-700" role="status">{location.state.message}</p>}
        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <label className="block space-y-2 text-sm font-medium text-slate-200">Email
            <input className={inputClass} type="email" autoComplete="email" required maxLength={320} value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="block space-y-2 text-sm font-medium text-slate-200">Password
            <input className={inputClass} type="password" autoComplete="current-password" required maxLength={128} value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <p className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-700" role="alert">{error}</p>}
          <button className="focus-ring w-full rounded-xl bg-indigo-600 px-4 py-3 font-semibold text-on-accent transition hover:bg-indigo-500 disabled:cursor-wait disabled:opacity-60" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-400">New to TaskFlow? <Link className="font-semibold text-indigo-400 hover:text-indigo-300" to="/register">Create an account</Link></p>
      </section>
    </main>
  );
}