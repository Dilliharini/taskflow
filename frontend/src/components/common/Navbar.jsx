import React, { useCallback, useEffect, useState } from 'react';
import StatusBadge from './StatusBadge';
import { Bell, CheckCheck, Layers, Kanban } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { getUnreadCount, listNotifications, markAllNotificationsRead, markNotificationRead } from '../../api/projects';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unread, setUnread] = useState(0);
  const [notificationError, setNotificationError] = useState('');
  const [loadingNotifications, setLoadingNotifications] = useState(false);

  const refreshNotifications = useCallback(async () => {
    if (!user) return;
    try {
      const [items, count] = await Promise.all([listNotifications({ limit: 20 }), getUnreadCount()]);
      setNotifications(items);
      setUnread(count.count);
      setNotificationError('');
    } catch (error) {
      setNotificationError(error.message || 'Notifications are unavailable.');
    }
  }, [user]);

  useEffect(() => {
    if (!user) {
      setNotifications([]);
      setUnread(0);
      return undefined;
    }
    refreshNotifications();
    const interval = window.setInterval(refreshNotifications, 45000);
    const onRealtimeNotification = () => refreshNotifications();
    window.addEventListener('taskflow:notification', onRealtimeNotification);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener('taskflow:notification', onRealtimeNotification);
    };
  }, [user, refreshNotifications]);

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  async function toggleNotifications() {
    const next = !open;
    setOpen(next);
    if (next) {
      setLoadingNotifications(true);
      await refreshNotifications();
      setLoadingNotifications(false);
    }
  }

  async function markRead(id) {
    try {
      await markNotificationRead(id);
      await refreshNotifications();
    } catch (error) {
      setNotificationError(error.message || 'Could not update notification.');
    }
  }

  async function markAllRead() {
    try {
      await markAllNotificationsRead();
      await refreshNotifications();
    } catch (error) {
      setNotificationError(error.message || 'Could not update notifications.');
    }
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
                Phase 4
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Collaborative Project Management</p>
          </div>
        </div>

        {/* Center Navigation Links (Preview for future phases) */}
        <nav className="hidden md:flex items-center gap-1 text-sm font-medium text-slate-400">
          {user && <Link to="/" className="flex items-center gap-1.5 px-3 py-1.5 text-white bg-slate-800/80 rounded-lg">
            <Kanban className="w-4 h-4 text-indigo-400" /> Dashboard
          </Link>}
          {user && <span className="px-3 py-1.5 text-slate-300">{user.name}</span>}
        </nav>

        {/* Right Status Badge */}
        <div className="flex items-center gap-3">
          <StatusBadge />
          {user && <div className="relative">
            <button type="button" onClick={toggleNotifications} aria-label={`Notifications, ${unread} unread`} aria-expanded={open} className="relative rounded-lg border border-slate-700 p-2 text-slate-300 transition hover:bg-slate-800 hover:text-white">
              <Bell size={18} />
              {unread > 0 && <span className="absolute -right-1 -top-1 min-w-4 rounded-full bg-rose-500 px-1 text-center text-[10px] font-bold leading-4 text-white">{unread > 99 ? '99+' : unread}</span>}
            </button>
            {open && <section className="absolute right-0 top-12 z-[60] w-[min(22rem,calc(100vw-1.5rem))] overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl" aria-label="Notifications">
              <header className="flex items-center justify-between border-b border-slate-700 px-4 py-3"><div><h2 className="text-sm font-semibold text-white">Notifications</h2><p className="text-xs text-slate-500">{unread} unread</p></div><button type="button" onClick={markAllRead} disabled={!unread} className="inline-flex items-center gap-1 text-xs text-indigo-300 hover:text-indigo-200 disabled:opacity-40"><CheckCheck size={14} /> Mark all read</button></header>
              {notificationError && <p className="px-4 py-3 text-xs text-rose-300" role="alert">{notificationError}</p>}
              {loadingNotifications ? <p className="px-4 py-6 text-center text-sm text-slate-400" role="status">Loading notifications…</p> : notifications.length === 0 ? <p className="px-4 py-8 text-center text-sm text-slate-400">You're all caught up.</p> : <ul className="max-h-96 divide-y divide-slate-800 overflow-y-auto">{notifications.map((item) => <li key={item.id} className={`flex items-start gap-3 px-4 py-3 ${item.is_read ? '' : 'bg-indigo-500/[0.06]'}`}><span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${item.is_read ? 'bg-slate-700' : 'bg-indigo-400'}`} /><div className="min-w-0 flex-1"><p className="text-sm text-slate-200">{item.message}</p><time className="mt-1 block text-[11px] text-slate-500" dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></div>{!item.is_read && <button type="button" aria-label="Mark notification as read" onClick={() => markRead(item.id)} className="text-xs text-indigo-300 hover:text-white">Read</button>}</li>)}</ul>}
            </section>}
          </div>}
          {user ? <button type="button" onClick={handleLogout} className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 transition hover:bg-slate-800">Sign out</button> : <Link to="/login" className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 transition hover:bg-slate-800">Sign in</Link>}
        </div>
      </div>
    </header>
  );
}
