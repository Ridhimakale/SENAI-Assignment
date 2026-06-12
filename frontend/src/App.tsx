import * as React from 'react';
import { useStore, ViewType } from './store';
import { useDashboardStats, useThreads } from './services/queries';
import { api } from './services/api';
import {
  Inbox,
  Mail,
  BarChart3,
  Terminal,
  Wifi,
  WifiOff,
  RefreshCw,
  Search,
  Bell,
  CircleUserRound,
  PlayCircle,
  Sparkles,
} from 'lucide-react';
import { MissionControl } from './features/inbox/MissionControl';
import { ThreadWorkspace } from './features/thread/ThreadWorkspace';
import { AnalyticsDashboard } from './features/analytics/AnalyticsDashboard';
import { SimulatorPanel } from './features/simulator/SimulatorPanel';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Input } from './components/ui/input';

export default function App() {
  const {
    activeView,
    setActiveView,
    connectionState,
    setConnectionState,
    actionMessage,
    setActionMessage,
    refreshIntervalMs,
    setRefreshIntervalMs,
    searchQuery,
    setSearchQuery,
    selectedId,
    setSelectedId,
  } = useStore();

  const [lastSync, setLastSync] = React.useState<Date>(new Date());
  const { data: stats, refetch: refetchStats } = useDashboardStats();
  const { data: threads, refetch: refetchThreads } = useThreads();

  React.useEffect(() => {
    async function checkHealth() {
      const isHealthy = await api.checkHealth();
      if (isHealthy) {
        setConnectionState('live');
      } else {
        setConnectionState('demo');
        setActionMessage('FastAPI backend offline. Running in Demo mode.');
      }
      setLastSync(new Date());
    }

    checkHealth();
    const timer = setInterval(checkHealth, 30000);
    return () => clearInterval(timer);
  }, [setActionMessage, setConnectionState]);

  const handleManualSync = async () => {
    setActionMessage('Syncing with server...');
    const isHealthy = await api.checkHealth();
    setConnectionState(isHealthy ? 'live' : 'demo');
    await Promise.all([refetchStats(), refetchThreads()]);
    setLastSync(new Date());
    setActionMessage('Workspace data refreshed.');
  };

  const navItems = [
    { id: 'inbox' as ViewType, label: 'Inbox Priority', icon: Inbox, badge: stats?.needs_human },
    { id: 'thread' as ViewType, label: 'Thread Workspace', icon: Mail },
    { id: 'analytics' as ViewType, label: 'Analytics', icon: BarChart3 },
    { id: 'simulator' as ViewType, label: 'Replay Simulator', icon: Terminal },
  ];

  const activeLabel = navItems.find((n) => n.id === activeView)?.label || 'Console';

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#F5F7FA] text-slate-800 font-sans">
      <aside className="sticky top-0 flex h-screen w-[280px] flex-col border-r border-slate-200 bg-[#2F3A4F] text-white shadow-[4px_0_20px_rgba(15,23,42,0.08)]">
        <div className="flex h-[72px] items-center gap-3 border-b border-white/10 px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#4A90E2] text-white shadow-lg shadow-blue-500/20">
            <span className="text-lg font-black leading-none">▲</span>
          </div>
          <div className="leading-tight">
            <h1 className="text-[1.05rem] font-bold tracking-tight text-white">SenAI Ops</h1>
            <p className="text-[0.72rem] font-medium uppercase tracking-[0.22em] text-slate-300">
              CRM Agent Intelligence
            </p>
          </div>
        </div>

        <nav className="flex-1 px-4 py-5 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveView(item.id);
                  if (item.id === 'thread' && !selectedId && threads?.length) {
                    setSelectedId(threads[0].id);
                  }
                }}
                className={`group relative flex w-full items-center justify-between rounded-xl px-4 py-3 text-left text-sm font-semibold transition-all ${
                  isActive
                    ? 'bg-[#4A90E2] text-white shadow-lg shadow-blue-500/20'
                    : 'text-slate-200 hover:bg-white/10 hover:text-white'
                }`}
              >
                {isActive && <span className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full bg-white/90" />}
                <div className="flex items-center gap-3">
                  <Icon size={17} className={isActive ? 'text-white' : 'text-slate-300 group-hover:text-white'} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && item.badge > 0 && (
                  <Badge
                    variant="destructive"
                    className="min-w-6 justify-center border-0 bg-white/20 px-2 py-1 text-[0.72rem] font-bold text-white"
                  >
                    {item.badge}
                  </Badge>
                )}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-white/10 bg-white/5 px-4 py-4 space-y-3">
          <div className="flex items-center justify-between text-xs font-medium text-slate-200">
            <div className="flex items-center gap-1.5">
              <RefreshCw size={13} className="text-slate-300" />
              <span>Poll Interval</span>
            </div>
            <select
              value={refreshIntervalMs}
              onChange={(e) => setRefreshIntervalMs(Number(e.target.value))}
              className="rounded-lg border border-white/10 bg-white/10 px-2 py-1 text-xs font-semibold text-white outline-none"
            >
              <option value={5000}>5s</option>
              <option value={10000}>10s</option>
              <option value={20000}>20s</option>
              <option value={30000}>30s</option>
            </select>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-300">
            <span>Last Synced</span>
            <span className="font-medium text-white">{lastSync.toLocaleTimeString()}</span>
          </div>

          <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2">
            <div className="space-y-0.5">
              <div className="text-[0.7rem] font-semibold uppercase tracking-[0.22em] text-slate-300">Mode</div>
              <div className="text-sm font-semibold text-white">
                {connectionState === 'live' ? 'Live' : connectionState === 'loading' ? 'Loading' : 'Demo fallback'}
              </div>
            </div>
            <button
              onClick={() => {
                const targetState = connectionState === 'live' ? 'demo' : 'live';
                setConnectionState(targetState);
                setActionMessage(`Switched to ${targetState === 'live' ? 'Live Backend' : 'Demo fallback'} mode.`);
              }}
              className="rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-white/15"
            >
              {connectionState === 'live' ? 'Live' : connectionState === 'loading' ? 'Loading' : 'Demo'}
            </button>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-[72px] items-center justify-between border-b border-slate-200 bg-white px-6 shadow-sm">
          <div className="flex min-w-0 flex-1 items-center gap-5">
            <div className="flex items-center gap-1.5 text-sm font-medium text-slate-400">
              <span>Workspace</span>
              <span>/</span>
              <span className="font-bold text-slate-900">{activeLabel}</span>
            </div>

            {(activeView === 'inbox' || activeView === 'thread') && (
              <div className="relative w-full max-w-[420px]">
                <Search size={15} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <Input
                  type="text"
                  placeholder="Search customer, email, ticket, company..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-11 rounded-xl border-slate-200 bg-slate-50 pl-10 pr-4 text-sm shadow-sm placeholder:text-slate-400"
                />
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 shadow-sm transition-colors hover:bg-slate-50">
              <Bell size={16} />
            </button>
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
              <CircleUserRound size={18} />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleManualSync}
              className="h-11 gap-2 rounded-xl border-slate-200 px-4 text-sm font-semibold text-slate-700"
            >
              <RefreshCw size={14} />
              <span>Sync Now</span>
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={() => setActiveView('simulator')}
              className="h-11 gap-2 rounded-xl bg-[#2F3A4F] px-4 text-sm font-semibold text-white hover:bg-[#243145]"
            >
              <PlayCircle size={14} />
              <span>Simulate Replay</span>
            </Button>
          </div>
        </header>

        <div className="flex items-center justify-between border-b border-slate-200 bg-[#EAF2FF] px-6 py-2 text-xs font-medium text-slate-700">
          <div className="flex items-center gap-2">
            <Sparkles size={13} className="text-[#4A90E2]" />
            <span>{actionMessage}</span>
          </div>
          <div className="flex items-center gap-4 text-[0.7rem] font-semibold uppercase tracking-[0.24em] text-slate-500">
            <span className="flex items-center gap-1">
              {connectionState === 'live' ? <Wifi size={12} /> : <WifiOff size={12} />}
              <span>{connectionState === 'live' ? 'Live Backend' : 'Demo Mode'}</span>
            </span>
            <span>SENAI-CORE-V1</span>
          </div>
        </div>

        <main className="relative flex-1 overflow-auto bg-[#F5F7FA]">
          {activeView === 'inbox' && <MissionControl />}
          {activeView === 'thread' && <ThreadWorkspace />}
          {activeView === 'analytics' && <AnalyticsDashboard />}
          {activeView === 'simulator' && <SimulatorPanel />}
        </main>
      </div>
    </div>
  );
}
