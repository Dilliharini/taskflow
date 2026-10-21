import React, { useCallback, useEffect, useState } from 'react';
import { Bell, CheckCheck, Layers, LogOut, LayoutDashboard, FolderKanban } from 'lucide-react';
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

  function notificationControl() {
    return (
      <div className="relative">
        <button
          type="button"
          onClick={toggleNotifications}
          aria-label={`Notifications, ${unread} unread`}
          aria-expanded={open}
          className="focus-ring relative rounded-xl border border-slate-700 bg-white p-2.5 text-slate-300 transition hover:bg-slate-900"
        >
          <Bell size={18} />
          {unread > 0 && <span className="absolute -right-1 -top-1 min-w-4 rounded-full bg-rose-500 px-1 text-center text-[10px] font-bold leading-4 text-on-accent">{unread > 99 ? '99+' : unread}</span>}
        </button>
        {open && (
          <section className="surface-shadow absolute right-0 top-12 z-[60] w-[min(22rem,calc(100vw-1.5rem))] overflow-hidden rounded-2xl border border-slate-700 bg-white" aria-label="Notifications">
            <header className="flex items-center justify-between border-b border-slate-700 px-4 py-3">
              <div><h2 className="text-sm font-semibold text-slate-100">Notifications</h2><p className="text-xs text-slate-500">{unread} unread</p></div>
              <button type="button" onClick={markAllRead} disabled={!unread} className="inline-flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-600 disabled:opacity-40"><CheckCheck size={14} /> Mark all read</button>
            </header>
            {notificationError && <p className="px-4 py-3 text-xs text-rose-600" role="alert">{notificationError}</p>}
            {loadingNotifications ? <p className="px-4 py-6 text-center text-sm text-slate-400" role="status">Loading notifications…</p> : notifications.length === 0 ? <p className="px-4 py-8 text-center text-sm text-slate-400">You're all caught up.</p> : (
              <ul className="max-h-96 divide-y divide-slate-700 overflow-y-auto">
                {notifications.map((item) => (
                  <li key={item.id} className={`flex items-start gap-3 px-4 py-3 ${item.is_read ? '' : 'bg-indigo-500/[0.06]'}`}>
                    <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${item.is_read ? 'bg-slate-600' : 'bg-indigo-500'}`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-slate-200">{item.message}</p>
                      <time className="mt-1 block text-[11px] text-slate-500" dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time>
                    </div>
                    {!item.is_read && <button type="button" aria-label="Mark notification as read" onClick={() => markRead(item.id)} className="text-xs font-medium text-indigo-400 hover:text-indigo-600">Read</button>}
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}
      </div>
    );
  }

  if (!user) {
    return (
      <header className="sticky top-0 z-40 border-b border-slate-700 bg-white/95 backdrop-blur lg:bg-white">
        <div className="mx-auto flex h-[72px] max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Brand />
          <nav className="flex items-center gap-2">
            <Link to="/login" className="focus-ring rounded-xl px-3 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-900">Sign in</Link>
            <Link to="/register" className="focus-ring rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-on-accent transition hover:bg-indigo-500">Get started</Link>
          </nav>
        </div>
      </header>
    );
  }

  return (
    <>
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[260px] flex-col border-r border-slate-700 bg-white px-4 py-6 lg:flex">
        <Brand />
        <p className="mb-3 mt-10 px-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Workspace</p>
        <nav className="space-y-1" aria-label="Main navigation">
          <Link to="/" className="flex items-center gap-3 rounded-xl bg-indigo-500/10 px-3 py-2.5 text-sm font-semibold text-indigo-400">
            <LayoutDashboard size={17} /> Overview
          </Link>
          <Link to="/#projects-title" className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-slate-900">
            <FolderKanban size={17} /> Projects
          </Link>
        </nav>
        <div className="mt-auto space-y-4">
          <div className="flex items-center gap-3 rounded-xl border border-slate-700 bg-slate-900/70 p-3">
            <Avatar name={user.name} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-100">{user.name}</p>
              <p className="truncate text-xs text-slate-500">{user.email}</p>
            </div>
          </div>
          <div className="flex items-center justify-between px-1">
            {notificationControl()}
            <button type="button" onClick={handleLogout} className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-900" title="Sign out">
              <LogOut size={16} /> Sign out
            </button>
          </div>
        </div>
      </aside>

      <header className="sticky top-0 z-40 border-b border-slate-700 bg-white/95 px-4 py-3 backdrop-blur lg:hidden">
        <div className="flex items-center justify-between gap-3">
          <Brand />
          <div className="flex items-center gap-2">
            {notificationControl()}
            <button type="button" onClick={handleLogout} className="rounded-xl border border-slate-700 p-2.5 text-slate-300 hover:bg-slate-900" aria-label="Sign out" title="Sign out">
              <LogOut size={17} />
            </button>
          </div>
        </div>
        <nav className="mt-3 flex gap-2 border-t border-slate-700 pt-3" aria-label="Main navigation">
          <Link to="/" className="flex items-center gap-2 rounded-lg bg-indigo-500/10 px-3 py-2 text-xs font-semibold text-indigo-400"><LayoutDashboard size={15} /> Overview</Link>
          <Link to="/#projects-title" className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-900"><FolderKanban size={15} /> Projects</Link>
        </nav>
      </header>
    </>
  );
}

function Brand() {
  return (
    <Link to="/" className="flex min-w-0 items-center gap-3 rounded-lg">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-on-accent">
        <Layers size={21} strokeWidth={2.2} />
      </span>
      <span className="min-w-0">
        <span className="block text-base font-bold tracking-tight text-slate-100">TaskFlow</span>
        <span className="block truncate text-[11px] font-medium text-slate-500">Work, in good flow.</span>
      </span>
    </Link>
  );
}

function Avatar({ name }) {
  const initials = name?.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'T';
  return <span aria-hidden="true" className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-violet-100 text-xs font-bold text-indigo-600">{initials}</span>;
}
