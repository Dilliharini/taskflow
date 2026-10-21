import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CalendarClock, FolderKanban, ListTodo, Plus, RefreshCw } from 'lucide-react';
import { createProject, getDashboard, listProjects } from '../api/projects';
import { useAuth } from '../auth/AuthContext';

const panel = 'rounded-2xl border border-slate-700 bg-white p-5 surface-shadow';
const button = 'focus-ring inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-on-accent transition hover:bg-indigo-500 disabled:cursor-wait disabled:opacity-60';
const statusLabels = { todo: 'To do', in_progress: 'In progress', done: 'Done' };

export default function DashboardPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [projectData, dashboardData] = await Promise.all([listProjects(), getDashboard()]);
      setProjects(projectData);
      setDashboard(dashboardData);
    } catch (err) {
      setError(err.message || 'Unable to load your workspace.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function handleCreate(event) {
    event.preventDefault();
    setCreating(true);
    setFormError('');
    try {
      await createProject({ name, description: description || null });
      setName('');
      setDescription('');
      await refresh();
    } catch (err) {
      setFormError(err.message || 'Project could not be created.');
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-400">Your workspace</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">Good to see you, {user?.name}</h1>
          <p className="mt-2 text-sm text-slate-400 sm:text-base">A clear view of the projects and work moving forward.</p>
        </div>
        <button type="button" className="focus-ring inline-flex items-center gap-2 self-start rounded-xl border border-slate-700 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-slate-900 sm:self-auto" onClick={refresh} disabled={loading}>
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </section>

      {error && <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-200" role="alert">{error}</div>}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Workspace summary">
        <Metric icon={<FolderKanban size={19} />} label="Projects" value={dashboard?.total_projects ?? '—'} tone="indigo" />
        <Metric icon={<ListTodo size={19} />} label="Open tasks" value={dashboard ? dashboard.total_tasks - (dashboard.tasks_by_status.done || 0) : '—'} tone="sky" />
        {Object.entries(statusLabels).map(([key, label]) => <Metric key={key} icon={<ListTodo size={19} />} label={label} value={dashboard?.tasks_by_status?.[key] ?? '—'} tone={key === 'done' ? 'emerald' : 'amber'} />)}
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.45fr_0.85fr]">
        <section className="space-y-4" aria-labelledby="projects-title">
          <div className="flex items-center justify-between">
            <div><h2 id="projects-title" className="text-xl font-bold tracking-tight text-white">Projects</h2><p className="mt-1 text-sm text-slate-400">Workspaces you own or collaborate on.</p></div>
            <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">{projects.length} total</span>
          </div>

          <form onSubmit={handleCreate} className={`${panel} space-y-3`}>
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-100"><Plus size={17} className="text-indigo-400" /> Start a project</div>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="sr-only" htmlFor="project-name">Project name</label>
              <input id="project-name" className="rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2.5 text-sm text-white outline-none focus:border-indigo-400" placeholder="Project name" maxLength={255} required value={name} onChange={(event) => setName(event.target.value)} />
              <label className="sr-only" htmlFor="project-description">Project description</label>
              <input id="project-description" className="rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2.5 text-sm text-white outline-none focus:border-indigo-400" placeholder="Short description (optional)" value={description} onChange={(event) => setDescription(event.target.value)} />
            </div>
            {formError && <p className="text-sm text-rose-300" role="alert">{formError}</p>}
            <button className={button} disabled={creating || !name.trim()}>{creating ? 'Creating…' : 'Create project'}</button>
          </form>

          {loading && projects.length === 0 ? <div className={`${panel} animate-pulse text-sm text-slate-400`} role="status">Loading projects…</div> : projects.length === 0 ? (
            <div className={`${panel} border-dashed py-10 text-center`}><FolderKanban className="mx-auto text-slate-600" size={30} /><h3 className="mt-3 font-semibold text-white">Your first project starts here</h3><p className="mt-1 text-sm text-slate-400">Create a workspace above, then invite your team.</p></div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {projects.map((project) => <Link key={project.id} to={`/projects/${project.id}`} className={`${panel} group transition hover:-translate-y-0.5 hover:border-indigo-500/60`}>
                <div className="flex items-start justify-between gap-3"><div className="min-w-0"><h3 className="truncate font-semibold text-white group-hover:text-indigo-300">{project.name}</h3><p className="mt-1 line-clamp-2 min-h-10 text-sm text-slate-400">{project.description || 'No description yet.'}</p></div><ArrowRight size={17} className="mt-1 shrink-0 text-slate-500 transition group-hover:translate-x-1 group-hover:text-indigo-300" /></div>
                <div className="mt-5 flex flex-wrap items-center justify-between gap-2 border-t border-slate-700/70 pt-3 text-xs text-slate-500"><span>Owner · {project.creator_name || 'Team member'}</span><time dateTime={project.updated_at}>Updated {new Date(project.updated_at).toLocaleDateString()}</time></div>
              </Link>)}
            </div>
          )}
        </section>

        <aside className="space-y-6">
          <TaskPanel title="Assigned to me" icon={<ListTodo size={17} />} tasks={dashboard?.assigned_to_me || []} empty="No tasks are assigned to you yet." />
          <TaskPanel title="Coming up" icon={<CalendarClock size={17} />} tasks={dashboard?.upcoming_due || []} empty="No due dates in the next two weeks." due />
        </aside>
      </div>

      <section className="space-y-3">
        <h2 className="text-xl font-bold text-white">Recently updated</h2>
        {dashboard?.recently_updated?.length ?         <div className="surface-shadow overflow-hidden rounded-2xl border border-slate-700 bg-white divide-y divide-slate-700/60">
          {dashboard.recently_updated.slice(0, 6).map((task) => <Link key={task.id} to={`/projects/${task.project_id}`} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 transition hover:bg-slate-800"><div><p className="font-medium text-slate-100">{task.title}</p><p className="mt-1 text-xs text-slate-500">{statusLabels[task.status]} · {task.priority} priority</p></div><time className="text-xs text-slate-500" dateTime={task.updated_at}>{new Date(task.updated_at).toLocaleString()}</time></Link>)}
        </div> : <p className={`${panel} text-sm text-slate-400`}>Your recent task updates will show here.</p>}
      </section>
    </div>
  );
}

function Metric({ icon, label, value, tone }) {
  const colors = { indigo: 'bg-indigo-500/10 text-indigo-300', sky: 'bg-sky-500/10 text-sky-300', amber: 'bg-amber-500/10 text-amber-300', emerald: 'bg-emerald-500/10 text-emerald-300' };
  return <div className={panel}><div className="flex items-center justify-between"><span className="text-sm text-slate-400">{label}</span><span className={`rounded-lg p-2 ${colors[tone]}`}>{icon}</span></div><p className="mt-3 text-3xl font-bold text-white">{value}</p></div>;
}

function TaskPanel({ title, icon, tasks, empty, due = false }) {
  return <section className={panel}><h2 className="flex items-center gap-2 font-semibold text-white">{icon}{title}</h2>
    {tasks.length ? <ul className="mt-3 divide-y divide-slate-700/60">{tasks.slice(0, 5).map((task) => <li key={task.id} className="py-3 first:pt-1 last:pb-0"><Link to={`/projects/${task.project_id}`} className="font-medium text-slate-200 hover:text-indigo-300">{task.title}</Link><p className="mt-1 text-xs text-slate-500">{due && task.due_date ? new Date(task.due_date).toLocaleDateString() : `${statusLabels[task.status]} · ${task.priority}`}</p></li>)}</ul> : <p className="mt-3 text-sm text-slate-500">{empty}</p>}
  </section>;
}