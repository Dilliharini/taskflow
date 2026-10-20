import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Clock3, MessageSquare, Pencil, Plus, RefreshCw, Trash2, Users } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import {
  addMember, createComment, createTask, deleteComment, deleteProject, deleteTask,
  getActivity, getProject, listComments, listMembers, listTasks, removeMember,
  updateComment, updateProject, updateTask,
} from '../api/projects';

const panel = 'rounded-2xl border border-slate-700/70 bg-slate-800/55 p-5';
const field = 'w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2.5 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-indigo-400';
const primary = 'inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-60';
const statusLabels = { todo: 'To do', in_progress: 'In progress', done: 'Done' };

export default function ProjectDetailPage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [members, setMembers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [role, setRole] = useState('member');
  const [filters, setFilters] = useState({ q: '', status: '', priority: '', assignee_id: '', due_from: '', due_to: '', sort: 'position', order: 'asc' });
  const [appliedFilters, setAppliedFilters] = useState({});
  const [taskForm, setTaskForm] = useState({ title: '', description: '', priority: 'medium', due_date: '', assignee_id: '' });
  const [memberEmail, setMemberEmail] = useState('');
  const [memberRole, setMemberRole] = useState('member');
  const [editingProject, setEditingProject] = useState(false);
  const [projectForm, setProjectForm] = useState({ name: '', description: '' });

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [projectData, memberData, taskData, activityData] = await Promise.all([
        getProject(projectId), listMembers(projectId), listTasks(projectId, appliedFilters), getActivity(projectId),
      ]);
      setProject(projectData);
      setMembers(memberData);
      setTasks(taskData);
      setActivity(activityData);
      setRole(memberData.find((member) => member.user_id === user?.id)?.role || 'member');
      setProjectForm({ name: projectData.name, description: projectData.description || '' });
    } catch (err) {
      setError(err.message || 'Unable to load this project.');
    } finally {
      setLoading(false);
    }
  }, [projectId, appliedFilters, user?.id]);

  useEffect(() => { refresh(); }, [refresh]);
  const canManage = role === 'owner' || role === 'admin';
  const canManageMembers = canManage;
  const isOwner = role === 'owner';

  async function perform(action, success) {
    setError('');
    setNotice('');
    try {
      await action();
      setNotice(success);
      await refresh();
    } catch (err) {
      setError(err.message || 'The request could not be completed.');
    }
  }

  async function handleCreateTask(event) {
    event.preventDefault();
    const payload = { ...taskForm, due_date: taskForm.due_date || null, assignee_id: taskForm.assignee_id || null };
    await perform(() => createTask(projectId, payload), 'Task created.');
    setTaskForm({ title: '', description: '', priority: 'medium', due_date: '', assignee_id: '' });
  }

  async function handleAddMember(event) {
    event.preventDefault();
    await perform(() => addMember(projectId, { email: memberEmail, role: memberRole }), 'Team member added.');
    setMemberEmail('');
    setMemberRole('member');
  }

  async function handleSaveProject(event) {
    event.preventDefault();
    await perform(() => updateProject(projectId, projectForm), 'Project details saved.');
    setEditingProject(false);
  }

  async function handleDeleteProject() {
    if (!window.confirm('Delete this project and all its tasks? This cannot be undone.')) return;
    try {
      await deleteProject(projectId);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'Project could not be deleted.');
    }
  }

  if (loading && !project) return <div className="grid min-h-[60vh] place-items-center text-slate-300" role="status">Loading project…</div>;
  if (error && !project) return <main className="mx-auto max-w-3xl px-4 py-12"><div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-5 text-rose-200" role="alert">{error}</div><Link className="mt-5 inline-flex text-indigo-300" to="/">Return to dashboard</Link></main>;
  if (!project) return null;

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white"><ArrowLeft size={16} /> Dashboard</Link>
      <section className="flex flex-col justify-between gap-5 rounded-3xl border border-slate-700/70 bg-gradient-to-br from-slate-800 to-slate-900 p-6 sm:flex-row sm:items-start sm:p-8">
        <div className="min-w-0 flex-1">
          {editingProject ? <form className="max-w-xl space-y-3" onSubmit={handleSaveProject}>
            <label className="sr-only" htmlFor="edit-project-name">Project name</label><input id="edit-project-name" className={field} required maxLength={255} value={projectForm.name} onChange={(e) => setProjectForm({ ...projectForm, name: e.target.value })} />
            <label className="sr-only" htmlFor="edit-project-description">Description</label><textarea id="edit-project-description" className={field} rows="3" value={projectForm.description} onChange={(e) => setProjectForm({ ...projectForm, description: e.target.value })} placeholder="Describe this project" />
            <button className={primary}>Save changes</button><button type="button" className="ml-2 px-3 py-2 text-sm text-slate-400" onClick={() => setEditingProject(false)}>Cancel</button>
          </form> : <>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-300">Project workspace · {role}</p>
            <h1 className="mt-2 break-words text-3xl font-bold text-white sm:text-4xl">{project.name}</h1>
            <p className="mt-3 max-w-2xl whitespace-pre-wrap text-slate-300">{project.description || 'No description provided.'}</p>
            <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500"><span>Created by {project.creator_name}</span><time dateTime={project.created_at}>Created {new Date(project.created_at).toLocaleDateString()}</time><time dateTime={project.updated_at}>Updated {new Date(project.updated_at).toLocaleDateString()}</time></div>
          </>}
        </div>
        {canManage && !editingProject && <div className="flex shrink-0 gap-2"><button className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800" onClick={() => setEditingProject(true)}><Pencil size={14} className="mr-1 inline" />Edit</button>{isOwner && <button className="rounded-lg border border-rose-500/30 px-3 py-2 text-sm text-rose-300 hover:bg-rose-500/10" onClick={handleDeleteProject}><Trash2 size={14} className="mr-1 inline" />Delete</button>}</div>}
      </section>
      {error && <p className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-200" role="alert">{error}</p>}
      {notice && <p className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-200" role="status">{notice}</p>}

      <div className="grid items-start gap-6 xl:grid-cols-[1fr_330px]">
        <section className="min-w-0 space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-xl font-bold text-white">Tasks</h2><p className="mt-1 text-sm text-slate-400">Search and filter tasks across this project.</p></div><span className="text-sm text-slate-500">{tasks.length} shown</span></div>
          <form className={`${panel} grid gap-3 sm:grid-cols-2 lg:grid-cols-6`} onSubmit={(event) => { event.preventDefault(); setAppliedFilters(Object.fromEntries(Object.entries(filters).filter(([, value]) => value))); }}>
            <label className="sr-only" htmlFor="task-search">Search tasks</label><input id="task-search" className={`${field} lg:col-span-2`} placeholder="Search title or description" value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} />
            <label className="sr-only" htmlFor="task-status">Filter status</label><select id="task-status" className={field} value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}><option value="">All statuses</option><option value="todo">To do</option><option value="in_progress">In progress</option><option value="done">Done</option></select>
            <label className="sr-only" htmlFor="task-priority">Filter priority</label><select id="task-priority" className={field} value={filters.priority} onChange={(e) => setFilters({ ...filters, priority: e.target.value })}><option value="">All priorities</option>{['low', 'medium', 'high', 'urgent'].map((p) => <option key={p} value={p}>{p}</option>)}</select>
            <label className="sr-only" htmlFor="task-assignee-filter">Filter assignee</label><select id="task-assignee-filter" className={field} value={filters.assignee_id} onChange={(e) => setFilters({ ...filters, assignee_id: e.target.value })}><option value="">All assignees</option>{members.map((member) => <option key={member.user_id} value={member.user_id}>{member.name}</option>)}</select>
            <label className="sr-only" htmlFor="task-due-from">Due from</label><input id="task-due-from" aria-label="Due from" className={field} type="date" value={filters.due_from} onChange={(e) => setFilters({ ...filters, due_from: e.target.value ? `${e.target.value}T00:00:00` : '' })} />
            <label className="sr-only" htmlFor="task-due-to">Due to</label><input id="task-due-to" aria-label="Due to" className={field} type="date" value={filters.due_to.slice(0, 10)} onChange={(e) => setFilters({ ...filters, due_to: e.target.value ? `${e.target.value}T23:59:59` : '' })} />
            <label className="sr-only" htmlFor="task-sort">Sort tasks</label><select id="task-sort" className={field} value={filters.sort} onChange={(e) => setFilters({ ...filters, sort: e.target.value })}><option value="position">Board position</option><option value="updated_at">Recently updated</option><option value="due_date">Due date</option><option value="title">Title</option><option value="priority">Priority</option></select>
            <label className="sr-only" htmlFor="task-order">Sort order</label><select id="task-order" className={field} value={filters.order} onChange={(e) => setFilters({ ...filters, order: e.target.value })}><option value="asc">Ascending</option><option value="desc">Descending</option></select>
            <div className="flex gap-2 sm:col-span-2 lg:col-span-6"><button className={primary}>Apply filters</button><button type="button" className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800" onClick={() => { const cleared = { q: '', status: '', priority: '', assignee_id: '', due_from: '', due_to: '', sort: 'position', order: 'asc' }; setFilters(cleared); setAppliedFilters({}); }}>Clear</button><button type="button" className="ml-auto rounded-lg border border-slate-700 p-2 text-slate-400 hover:text-white" title="Refresh" onClick={refresh}><RefreshCw size={15} /></button></div>
          </form>

          <form className={`${panel} grid gap-3 sm:grid-cols-2`} onSubmit={handleCreateTask}>
            <div className="sm:col-span-2"><h3 className="flex items-center gap-2 font-semibold text-white"><Plus size={17} className="text-indigo-300" /> Add a task</h3></div>
            <label className="sr-only" htmlFor="new-task-title">Task title</label><input id="new-task-title" className={field} placeholder="Task title" required maxLength={255} value={taskForm.title} onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })} />
            <label className="sr-only" htmlFor="new-task-priority">Priority</label><select id="new-task-priority" className={field} value={taskForm.priority} onChange={(e) => setTaskForm({ ...taskForm, priority: e.target.value })}>{['low', 'medium', 'high', 'urgent'].map((p) => <option key={p} value={p}>{p[0].toUpperCase() + p.slice(1)} priority</option>)}</select>
            <label className="sr-only" htmlFor="new-task-description">Description</label><textarea id="new-task-description" className={`${field} sm:col-span-2`} rows="2" placeholder="Description (optional)" value={taskForm.description} onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })} />
            <label className="sr-only" htmlFor="new-task-assignee">Assignee</label><select id="new-task-assignee" className={field} value={taskForm.assignee_id} onChange={(e) => setTaskForm({ ...taskForm, assignee_id: e.target.value })}><option value="">Unassigned</option>{members.map((member) => <option key={member.user_id} value={member.user_id}>{member.name}</option>)}</select>
            <label className="sr-only" htmlFor="new-task-due">Due date</label><input id="new-task-due" className={field} type="datetime-local" value={taskForm.due_date} onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })} />
            <div className="sm:col-span-2"><button className={primary} disabled={!taskForm.title.trim()}>Create task</button></div>
          </form>

          {loading ? <div className={`${panel} text-sm text-slate-400`} role="status">Refreshing tasks…</div> : tasks.length === 0 ? <div className={`${panel} border-dashed py-8 text-center text-sm text-slate-400`}>No tasks match these filters. Create a task or clear the filters.</div> : <div className="space-y-3">{tasks.map((task) => <TaskItem key={task.id} task={task} projectId={projectId} members={members} user={user} canManage={canManage} onChange={refresh} onError={setError} />)}</div>}
        </section>

        <aside className="space-y-6">
          <section className={panel}><h2 className="flex items-center gap-2 font-semibold text-white"><Users size={17} /> Team <span className="ml-auto text-xs font-normal text-slate-500">{members.length}</span></h2>
            <ul className="mt-4 space-y-3">{members.map((member) => <li key={member.id} className="flex items-center justify-between gap-3"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-200">{member.name}</p><p className="truncate text-xs text-slate-500">{member.email} · {member.role}</p></div>{canManageMembers && member.role !== 'owner' && (isOwner || member.role === 'member') && <button aria-label={`Remove ${member.name}`} title="Remove member" className="rounded-lg p-2 text-slate-500 hover:bg-rose-500/10 hover:text-rose-300" onClick={() => perform(() => removeMember(projectId, member.user_id), 'Team member removed.')}><Trash2 size={14} /></button>}</li>)}</ul>
            {canManageMembers && <form className="mt-5 space-y-2 border-t border-slate-700/70 pt-4" onSubmit={handleAddMember}><label className="block text-xs font-medium text-slate-400" htmlFor="member-email">Invite registered user by email</label><input id="member-email" className={field} type="email" required placeholder="teammate@example.com" value={memberEmail} onChange={(e) => setMemberEmail(e.target.value)} /><div className="flex gap-2"><label className="sr-only" htmlFor="member-role">Role</label><select id="member-role" className={field} value={memberRole} onChange={(e) => setMemberRole(e.target.value)}><option value="member">Member</option>{isOwner && <option value="admin">Admin</option>}</select><button className={primary} aria-label="Add team member"><Plus size={16} /></button></div></form>}
          </section>

          <section className={panel}><h2 className="flex items-center gap-2 font-semibold text-white"><Clock3 size={17} /> Activity</h2>{activity.length ? <ol className="mt-4 space-y-4">{activity.slice(0, 12).map((item) => <li key={item.id} className="border-l border-indigo-500/40 pl-3"><p className="text-sm text-slate-300"><span className="font-medium text-white">{item.actor_name || 'A teammate'}</span> {activityText(item)}</p><time className="mt-1 block text-xs text-slate-500" dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></li>)}</ol> : <p className="mt-3 text-sm text-slate-500">Project activity will appear here.</p>}</section>
        </aside>
      </div>
    </main>
  );
}

function activityText(item) {
  const entity = item.entity_type === 'project_member' ? 'a team member' : item.entity_type;
  const action = { created: 'created', updated: 'updated', deleted: 'deleted', member_added: 'added', member_removed: 'removed', commented: 'commented on', comment_updated: 'edited a comment on', comment_deleted: 'deleted a comment on' }[item.action] || item.action.replaceAll('_', ' ');
  const suffix = item.entity_type === 'task' && item.details?.title ? `: ${item.details.title}` : '';
  return `${action} ${entity}${suffix}`;
}

function TaskItem({ task, projectId, members, user, canManage, onChange, onError }) {
  const [comments, setComments] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [editing, setEditing] = useState(false);
  const [editValues, setEditValues] = useState({ title: task.title, description: task.description || '', due_date: task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : '' });
  const [busy, setBusy] = useState(false);
  const assignee = members.find((member) => member.user_id === task.assignee_id);

  async function saveTask(values) {
    setBusy(true);
    onError('');
    try { await updateTask(projectId, task.id, values); await onChange(); }
    catch (err) { onError(err.message || 'Task could not be updated.'); }
    finally { setBusy(false); }
  }
  async function toggleComments() {
    if (comments === null) {
      try { setComments(await listComments(projectId, task.id)); }
      catch (err) { onError(err.message || 'Comments could not be loaded.'); }
    } else setComments(null);
  }
  async function postComment(event) {
    event.preventDefault();
    try { const created = await createComment(projectId, task.id, { content: commentText }); setComments([...(comments || []), created]); setCommentText(''); await onChange(); }
    catch (err) { onError(err.message || 'Comment could not be posted.'); }
  }
  async function removeTask() {
    if (!window.confirm(`Delete “${task.title}”?`)) return;
    try { await deleteTask(projectId, task.id); await onChange(); }
    catch (err) { onError(err.message || 'Task could not be deleted.'); }
  }
  async function removeComment(comment) {
    try { await deleteComment(projectId, task.id, comment.id); setComments(comments.filter((item) => item.id !== comment.id)); await onChange(); }
    catch (err) { onError(err.message || 'Comment could not be deleted.'); }
  }
  async function editComment(comment) {
    const content = window.prompt('Edit comment', comment.content);
    if (content === null || !content.trim()) return;
    try { const updated = await updateComment(projectId, task.id, comment.id, { content }); setComments(comments.map((item) => item.id === comment.id ? updated : item)); await onChange(); }
    catch (err) { onError(err.message || 'Comment could not be edited.'); }
  }

  return <article className={panel}>
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0 flex-1">
        {editing ? <form className="space-y-2" onSubmit={async (event) => { event.preventDefault(); await saveTask({ ...editValues, due_date: editValues.due_date || null }); setEditing(false); }}><input className={field} required maxLength={255} value={editValues.title} onChange={(e) => setEditValues({ ...editValues, title: e.target.value })} /><textarea className={field} rows="2" value={editValues.description} onChange={(e) => setEditValues({ ...editValues, description: e.target.value })} placeholder="Description" /><label className="block text-xs text-slate-400">Due date<input aria-label="Edit due date" className={`${field} mt-1`} type="datetime-local" value={editValues.due_date} onChange={(e) => setEditValues({ ...editValues, due_date: e.target.value })} /></label><button className={primary} disabled={busy}>Save task</button><button type="button" className="ml-2 px-3 py-2 text-sm text-slate-400" onClick={() => setEditing(false)}>Cancel</button></form> : <><h3 className="break-words font-semibold text-white">{task.title}</h3><p className="mt-1 whitespace-pre-wrap text-sm text-slate-400">{task.description || 'No description.'}</p></>}
      </div>
      <div className="flex items-center gap-1">{!editing && <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-700 hover:text-white" title="Edit task" onClick={() => setEditing(true)}><Pencil size={15} /></button>}{canManage && <button className="rounded-lg p-2 text-slate-500 hover:bg-rose-500/10 hover:text-rose-300" title="Delete task" onClick={removeTask}><Trash2 size={15} /></button>}</div>
    </div>
    <div className="mt-4 flex flex-wrap items-center gap-2">
      <label className="sr-only" htmlFor={`status-${task.id}`}>Task status</label><select id={`status-${task.id}`} aria-label="Task status" className="rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-2 text-xs text-slate-200" value={task.status} onChange={(e) => saveTask({ status: e.target.value })}>{Object.entries(statusLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select>
      <label className="sr-only" htmlFor={`priority-${task.id}`}>Task priority</label><select id={`priority-${task.id}`} aria-label="Task priority" className="rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-2 text-xs text-slate-200" value={task.priority} onChange={(e) => saveTask({ priority: e.target.value })}>{['low', 'medium', 'high', 'urgent'].map((p) => <option key={p} value={p}>{p}</option>)}</select>
      <label className="sr-only" htmlFor={`assignee-${task.id}`}>Task assignee</label><select id={`assignee-${task.id}`} aria-label="Task assignee" className="max-w-40 rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-2 text-xs text-slate-200" value={task.assignee_id || ''} onChange={(e) => saveTask({ assignee_id: e.target.value || null })}><option value="">Unassigned</option>{members.map((member) => <option key={member.user_id} value={member.user_id}>{member.name}</option>)}</select>
      <span className="ml-auto text-xs text-slate-500">{assignee ? `Assigned to ${assignee.name}` : 'Unassigned'}</span>
    </div>
    <div className="mt-3 flex items-center justify-between border-t border-slate-700/70 pt-3"><span className="text-xs text-slate-500">{task.due_date ? `Due ${new Date(task.due_date).toLocaleDateString()}` : 'No due date'}</span><button type="button" className="inline-flex items-center gap-1.5 text-xs text-indigo-300 hover:text-indigo-200" onClick={toggleComments}><MessageSquare size={14} /> {comments ? 'Hide' : 'Comments'}</button></div>
    {comments && <div className="mt-4 space-y-3 border-t border-slate-700/70 pt-4">{comments.map((comment) => <div key={comment.id} className="rounded-xl bg-slate-900/70 p-3"><div className="flex justify-between gap-2"><p className="text-xs font-semibold text-slate-200">{comment.author_name} <time className="ml-1 font-normal text-slate-500">{new Date(comment.created_at).toLocaleString()}</time></p>{(comment.author_id === user?.id || canManage) && <div className="flex"><button aria-label="Edit comment" className="px-1 text-slate-500 hover:text-white" onClick={() => editComment(comment)}><Pencil size={13} /></button><button aria-label="Delete comment" className="px-1 text-slate-500 hover:text-rose-300" onClick={() => removeComment(comment)}><Trash2 size={13} /></button></div>}</div><p className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{comment.content}</p></div>)}
      <form className="flex gap-2" onSubmit={postComment}><label className="sr-only" htmlFor={`comment-${task.id}`}>Add a comment</label><input id={`comment-${task.id}`} className={field} maxLength={10000} required placeholder="Write a comment…" value={commentText} onChange={(e) => setCommentText(e.target.value)} /><button aria-label="Post comment" className={primary} disabled={!commentText.trim()}><Plus size={16} /></button></form>
    </div>}
  </article>;
}