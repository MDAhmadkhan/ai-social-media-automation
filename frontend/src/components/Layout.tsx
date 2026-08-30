import { BarChart3, CalendarClock, FileText, Globe2, Home, KeyRound, LogOut, Settings, Share2, Sparkles } from "lucide-react";

const items = [
  ["Dashboard", Home],
  ["Websites", Globe2],
  ["Content", FileText],
  ["AI Studio", Sparkles],
  ["Schedules", CalendarClock],
  ["Accounts", Share2],
  ["Analytics", BarChart3],
  ["Settings", Settings],
  ["Logs", KeyRound]
] as const;

export function Layout({ section, setSection, onLogout, children }: { section: string; setSection: (value: string) => void; onLogout: () => void; children: React.ReactNode }) {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="border-r border-slate-200 bg-white px-4 py-5">
        <div className="mb-6">
          <p className="text-sm font-semibold text-brand-700">AI Social Media</p>
          <h1 className="text-xl font-bold text-slate-950">Automation SaaS</h1>
        </div>
        <nav className="grid gap-1">
          {items.map(([label, Icon]) => (
            <button
              key={label}
              onClick={() => setSection(label)}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-left text-sm font-medium ${
                section === label ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>
        <button onClick={onLogout} className="mt-8 flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100">
          <LogOut size={18} />
          Logout
        </button>
      </aside>
      <main className="p-4 lg:p-8">{children}</main>
    </div>
  );
}
