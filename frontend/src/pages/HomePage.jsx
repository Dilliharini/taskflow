import { ArrowRight, CalendarCheck2, Check, Layers3, MessageCircle, UsersRound } from 'lucide-react';
import { Link } from 'react-router-dom';

const capabilities = [
  {
    icon: Layers3,
    title: 'Projects with a clear shape',
    description: 'Keep project details, ownership, and team membership together in one shared workspace.',
  },
  {
    icon: CalendarCheck2,
    title: 'A practical view of the work',
    description: 'Create, assign, prioritize, search, and filter tasks without losing sight of due dates.',
  },
  {
    icon: MessageCircle,
    title: 'Context stays close',
    description: 'Discuss tasks, follow project activity, and keep the latest changes easy to find.',
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 sm:py-16 lg:px-8">
      <section className="surface-shadow relative overflow-hidden rounded-[2rem] border border-slate-700 bg-white px-6 py-12 sm:px-10 sm:py-16 lg:px-16">
        <div aria-hidden="true" className="pointer-events-none absolute -right-28 -top-36 h-96 w-96 rounded-full border-[48px] border-indigo-500/[0.06]" />
        <div className="relative max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/[0.06] px-3 py-1.5 text-xs font-semibold text-indigo-500">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
            Project management, with room to think
          </div>
          <h1 className="mt-6 text-4xl font-bold leading-[1.08] tracking-tight text-white sm:text-6xl">
            Make good work feel
            <span className="text-indigo-400"> effortless.</span>
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-400 sm:text-lg">
            TaskFlow brings projects, tasks, and team conversations into one calm workspace—so everyone can focus on what moves the work forward.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link to="/register" className="focus-ring inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-on-accent transition hover:bg-indigo-500">
              Create your workspace <ArrowRight size={16} />
            </Link>
            <Link to="/login" className="focus-ring rounded-xl px-4 py-3 text-sm font-semibold text-slate-300 transition hover:bg-slate-900">
              Sign in
            </Link>
          </div>
          <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 border-t border-slate-700 pt-6 text-sm text-slate-400">
            <span className="inline-flex items-center gap-2"><Check size={15} className="text-emerald-600" /> Clear ownership</span>
            <span className="inline-flex items-center gap-2"><Check size={15} className="text-emerald-600" /> Useful task context</span>
            <span className="inline-flex items-center gap-2"><Check size={15} className="text-emerald-600" /> Team visibility</span>
          </div>
        </div>
      </section>

      <section className="py-14 sm:py-20" aria-labelledby="capabilities-title">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-400">Made for momentum</p>
          <h2 id="capabilities-title" className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">Everything has a place. Nothing gets in the way.</h2>
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {capabilities.map(({ icon: Icon, title, description }) => (
            <article key={title} className="rounded-2xl border border-slate-700 bg-white p-6 transition hover:-translate-y-0.5 hover:shadow-lg">
              <span className="inline-flex rounded-xl bg-indigo-500/[0.08] p-3 text-indigo-500"><Icon size={20} /></span>
              <h3 className="mt-5 font-semibold text-slate-100">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
            </article>
          ))}
        </div>
        <div className="mt-12 flex items-center gap-3 rounded-2xl border border-slate-700 bg-white p-5">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-indigo-500/[0.08] text-indigo-500"><UsersRound size={19} /></span>
          <p className="text-sm leading-6 text-slate-400">Bring your team into the conversation with project roles, task assignments, comments, and activity history.</p>
        </div>
      </section>
    </main>
  );
}
