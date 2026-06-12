import * as React from 'react';
import { useStore, InboxTabType, SortByType } from '../../store';
import { useDashboardStats, useThreads } from '../../services/queries';
import { Thread } from '../../types';
import {
  Inbox,
  ArrowUpDown,
  Archive,
  UserCheck,
  ShieldAlert,
  ChevronRight,
  MessageSquare,
  AlertTriangle,
  Clock3,
  Sparkles,
  UserRound,
  Send,
  Megaphone,
  Tag,
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';

const priorityClass = (priority: number) => {
  if (priority >= 95) return 'bg-red-50 text-red-700 border-red-200';
  if (priority >= 80) return 'bg-orange-50 text-orange-700 border-orange-200';
  if (priority >= 50) return 'bg-blue-50 text-blue-700 border-blue-200';
  return 'bg-slate-100 text-slate-600 border-slate-200';
};

const urgencyClass = (urgency: string) => {
  if (urgency === 'Critical') return 'bg-red-500 text-white';
  if (urgency === 'High') return 'bg-orange-400 text-white';
  if (urgency === 'Medium') return 'bg-blue-400 text-white';
  return 'bg-slate-200 text-slate-700';
};

const computeConfidence = (thread: Thread) => {
  const score = 0.95 - Math.abs(thread.sentimentScore) * 0.18;
  return Math.max(0.72, Math.min(0.97, score));
};

const computeSlaRemaining = (thread: Thread) => {
  if (thread.urgency === 'Critical') return '0h';
  if (thread.urgency === 'High') return '4h';
  if (thread.urgency === 'Medium') return '12h';
  return '24h';
};

export function MissionControl() {
  const {
    inboxTab,
    setInboxTab,
    sortBy,
    setSortBy,
    searchQuery,
    setSearchQuery,
    selectedId,
    setSelectedId,
    setActiveView,
    setActionMessage,
  } = useStore();

  const { data: stats } = useDashboardStats();
  const { data: threadsData, refetch: refetchThreads } = useThreads();
  const [localThreads, setLocalThreads] = React.useState<Thread[]>([]);

  React.useEffect(() => {
    if (threadsData) {
      setLocalThreads(threadsData);
    }
  }, [threadsData]);

  const updateThread = React.useCallback((threadId: string, updater: (thread: Thread) => Thread) => {
    setLocalThreads((curr) => curr.map((thread) => (thread.id === threadId ? updater(thread) : thread)));
  }, []);

  const filteredThreads = React.useMemo(() => {
    const query = searchQuery.toLowerCase().trim();
    return localThreads
      .filter((thread) => {
        if (inboxTab === 'Needs Human' && !thread.requiresHuman) return false;
        if (inboxTab === 'Auto-Replied' && thread.status !== 'Replied') return false;
        if (inboxTab === 'Escalated' && thread.status !== 'Escalated') return false;
        if (inboxTab === 'Spam' && thread.category !== 'Spam') return false;

        if (!query) return true;
        const bodyMatch = thread.messages.some((m) => m.body.toLowerCase().includes(query));
        const senderMatch = thread.sender.toLowerCase().includes(query);
        const companyMatch = thread.company.toLowerCase().includes(query);
        const subjectMatch = thread.subject.toLowerCase().includes(query);
        return bodyMatch || senderMatch || companyMatch || subjectMatch;
      })
      .sort((a, b) => {
        if (sortBy === 'priority') return b.priority - a.priority;
        if (sortBy === 'sentiment') return a.sentimentScore - b.sentimentScore;
        return new Date(b.lastActivity).getTime() - new Date(a.lastActivity).getTime();
      });
  }, [localThreads, inboxTab, searchQuery, sortBy]);

  const currentSelected = filteredThreads.find((t) => t.id === selectedId) || filteredThreads[0];

  React.useEffect(() => {
    if (currentSelected && selectedId !== currentSelected.id) {
      setSelectedId(currentSelected.id);
    }
  }, [currentSelected, selectedId, setSelectedId]);

  const handleMarkSpam = (threadId = selectedId) => {
    if (!threadId) return;
    updateThread(threadId, (thread) => ({ ...thread, status: 'Spam', category: 'Spam', requiresHuman: false }));
    setActionMessage('Thread marked as Spam.');
  };

  const handleAssignSelected = (threadId = selectedId) => {
    if (!threadId) return;
    const name = window.prompt('Assign this thread to:', 'support-tier-2');
    if (!name) return;
    updateThread(threadId, (thread) => ({ ...thread, assignedTo: name }));
    setActionMessage(`Assigned thread to ${name}.`);
  };

  const handleArchiveSelected = (threadId = selectedId) => {
    if (!threadId) return;
    updateThread(threadId, (thread) => ({ ...thread, status: 'Archived' }));
    setActionMessage('Thread archived.');
  };

  const handleEscalateSelected = (threadId = selectedId) => {
    if (!threadId) return;
    updateThread(threadId, (thread) => ({ ...thread, status: 'Escalated', requiresHuman: true }));
    setActionMessage('Thread escalated to human review.');
  };

  const handleOpenThread = (threadId: string) => {
    setSelectedId(threadId);
    setActiveView('thread');
  };

  const tabs: InboxTabType[] = ['All', 'Needs Human', 'Auto-Replied', 'Escalated', 'Spam'];
  const kpis = [
    {
      label: 'Pending Responses',
      value: stats?.pending ?? 0,
      icon: Inbox,
      tone: 'text-slate-900',
      accent: 'bg-blue-50 text-[#4A90E2]',
      trend: '12% this week',
    },
    {
      label: 'Needs Human',
      value: stats?.needs_human ?? 0,
      icon: UserCheck,
      tone: 'text-orange-600',
      accent: 'bg-orange-50 text-[#F5A623]',
      trend: 'Escalation watch',
    },
    {
      label: 'Auto Replied',
      value: stats?.replied ?? 0,
      icon: Send,
      tone: 'text-emerald-600',
      accent: 'bg-emerald-50 text-[#36C275]',
      trend: 'Automation running',
    },
    {
      label: 'Escalated',
      value: stats?.escalated ?? 0,
      icon: AlertTriangle,
      tone: 'text-red-600',
      accent: 'bg-red-50 text-[#E74C3C]',
      trend: 'Needs review',
    },
    {
      label: 'Spam',
      value: stats?.spam ?? 0,
      icon: ShieldAlert,
      tone: 'text-slate-500',
      accent: 'bg-slate-100 text-slate-500',
      trend: 'Filtered out',
    },
  ];

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">
          <Sparkles size={13} className="text-[#4A90E2]" />
          <span>Mission Control Inbox</span>
        </div>
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="text-[2rem] font-bold tracking-tight text-slate-900">Inbox Priority</h2>
            <p className="mt-1 text-sm text-slate-500">
              High-signal CRM queue with sentiment, urgency, SLA pressure, and actionability at a glance.
            </p>
          </div>
          <div className="hidden items-center gap-2 lg:flex">
            <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-3 py-1 text-xs font-semibold">
              Live thread grouping
            </Badge>
            <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-3 py-1 text-xs font-semibold">
              SLA-aware sorting
            </Badge>
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {kpis.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.label} className="border-slate-200 bg-white">
              <CardContent className="flex min-h-[120px] flex-col justify-between p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-2">
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                      {card.label}
                    </span>
                    <div className={`text-[2rem] font-bold tracking-tight ${card.tone}`}>{card.value}</div>
                  </div>
                  <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${card.accent}`}>
                    <Icon size={18} />
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs font-medium text-slate-500">
                  <span>{card.trend}</span>
                  <span className="rounded-full bg-slate-50 px-2.5 py-1 text-[0.72rem] font-semibold text-slate-500">
                    Updated live
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="border-slate-200 bg-white">
        <CardContent className="p-4 sm:p-5">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-wrap items-center gap-2">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setInboxTab(tab)}
                  className={`rounded-lg px-4 py-2 text-sm font-semibold transition-all ${
                    inboxTab === tab
                      ? 'bg-[#4A90E2] text-white shadow-sm'
                      : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-600">
                <ArrowUpDown size={14} className="text-slate-400" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortByType)}
                  className="bg-transparent text-sm font-semibold text-slate-700 outline-none"
                >
                  <option value="priority">Priority</option>
                  <option value="lastActivity">Last activity</option>
                  <option value="sentiment">Sentiment (Negative)</option>
                </select>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAssignSelected()}
                className="h-11 gap-2 rounded-xl border-slate-200 px-4 text-sm text-slate-700"
                disabled={!selectedId}
              >
                <UserCheck size={14} />
                <span>Assign</span>
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => handleMarkSpam()}
                className="h-11 gap-2 rounded-xl border-slate-200 px-4 text-sm text-slate-700"
                disabled={!selectedId}
              >
                <ShieldAlert size={14} />
                <span>Spam</span>
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => handleArchiveSelected()}
                className="h-11 gap-2 rounded-xl border-slate-200 px-4 text-sm text-slate-700"
                disabled={!selectedId}
              >
                <Archive size={14} />
                <span>Archive</span>
              </Button>

              <Button
                variant="default"
                size="sm"
                onClick={() => handleEscalateSelected()}
                className="h-11 gap-2 rounded-xl bg-[#E74C3C] px-4 text-sm text-white hover:bg-[#d44334]"
                disabled={!selectedId}
              >
                <Megaphone size={14} />
                <span>Escalate</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="overflow-hidden border-slate-200 bg-white">
        <Table>
          <TableHeader className="bg-slate-50">
            <TableRow>
              <TableHead className="w-[23%] text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Customer
              </TableHead>
              <TableHead className="w-[26%] text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Subject
              </TableHead>
              <TableHead className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Sentiment
              </TableHead>
              <TableHead className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Category
              </TableHead>
              <TableHead className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Urgency
              </TableHead>
              <TableHead className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                SLA Remaining
              </TableHead>
              <TableHead className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                AI Confidence
              </TableHead>
              <TableHead className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Priority Score
              </TableHead>
              <TableHead className="text-right text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Actions
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredThreads.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="h-40 text-center text-sm text-slate-400">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Inbox size={26} className="text-slate-300" />
                    <span>No threads found in this tab.</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredThreads.map((thread) => {
                const isSelected = thread.id === selectedId;
                const latestMsg = thread.messages[thread.messages.length - 1];
                const dateStr = new Date(thread.lastActivity).toLocaleDateString(undefined, {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                });
                const confidence = computeConfidence(thread);
                const slaRemaining = computeSlaRemaining(thread);

                return (
                  <TableRow
                    key={thread.id}
                    className={`group cursor-pointer border-b border-slate-100 transition-colors hover:bg-[#EAF2FF] ${
                      isSelected ? 'bg-[#EAF2FF]' : ''
                    }`}
                    onClick={() => setSelectedId(thread.id)}
                    onDoubleClick={() => handleOpenThread(thread.id)}
                  >
                    <TableCell>
                      <div className="flex items-start gap-3">
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#4A90E2]/10 text-sm font-bold text-[#4A90E2]">
                          {thread.company
                            .split(' ')
                            .map((part) => part[0])
                            .join('')
                            .slice(0, 2)
                            .toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="truncate text-sm font-bold text-slate-900">{thread.company}</span>
                            {thread.contact.status === 'VIP' && (
                              <span className="h-2 w-2 rounded-full bg-[#4A90E2]" title="VIP Account" />
                            )}
                          </div>
                          <div className="truncate text-xs text-slate-400">{thread.sender}</div>
                          <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                            <span className="flex items-center gap-1">
                              <MessageSquare size={11} />
                              {thread.messages.length} messages
                            </span>
                            <span>•</span>
                            <span>{dateStr}</span>
                          </div>
                        </div>
                      </div>
                    </TableCell>

                    <TableCell>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenThread(thread.id);
                        }}
                        className="group flex items-center gap-2 text-left text-sm font-semibold text-[#4A90E2] transition-colors hover:text-[#3f82cf]"
                      >
                        <span className="truncate">{thread.subject}</span>
                        <ChevronRight size={14} className="opacity-0 transition-opacity group-hover:opacity-100" />
                      </button>
                      <p className="mt-1 line-clamp-1 text-xs text-slate-500 italic">
                        {latestMsg?.body || 'No message preview available'}
                      </p>
                    </TableCell>

                    <TableCell>
                      <Badge
                        variant={thread.sentiment === 'Negative' ? 'destructive' : thread.sentiment === 'Positive' ? 'success' : 'secondary'}
                        className="rounded-full px-3 py-1 text-xs font-semibold"
                      >
                        {thread.sentiment} ({thread.sentimentScore.toFixed(2)})
                      </Badge>
                    </TableCell>

                    <TableCell>
                      <Badge variant="outline" className="rounded-full border-slate-200 px-3 py-1 text-xs font-semibold capitalize text-slate-700">
                        {thread.category}
                      </Badge>
                    </TableCell>

                    <TableCell>
                      <Badge className={`rounded-full border px-3 py-1 text-xs font-semibold ${urgencyClass(thread.urgency)}`}>
                        {thread.urgency}
                      </Badge>
                    </TableCell>

                    <TableCell>
                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                        <Clock3 size={13} className="text-slate-400" />
                        <span>{slaRemaining}</span>
                      </div>
                    </TableCell>

                    <TableCell>
                      <div className="flex flex-col">
                        <span className="text-sm font-semibold text-slate-900">{Math.round(confidence * 100)}%</span>
                        <span className="text-xs text-slate-400">grounding score</span>
                      </div>
                    </TableCell>

                    <TableCell>
                      <Badge variant="outline" className={`rounded-full px-3 py-1 text-xs font-bold ${priorityClass(thread.priority)}`}>
                        P{thread.priority}
                      </Badge>
                    </TableCell>

                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1 opacity-100 xl:opacity-0 xl:group-hover:opacity-100 transition-opacity">
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-9 rounded-lg border-slate-200 px-3 text-xs text-slate-700"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAssignSelected(thread.id);
                          }}
                        >
                          Assign
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-9 rounded-lg border-slate-200 px-3 text-xs text-slate-700"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenThread(thread.id);
                          }}
                        >
                          Reply
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-9 rounded-lg border-slate-200 px-3 text-xs text-slate-700"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEscalateSelected(thread.id);
                          }}
                        >
                          Escalate
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-9 rounded-lg border-slate-200 px-3 text-xs text-slate-700"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleArchiveSelected(thread.id);
                          }}
                        >
                          Archive
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </Card>

      <div className="rounded-2xl border border-[#D7E4F5] bg-[#EAF2FF] px-5 py-4 text-sm text-slate-700 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-xl bg-white text-[#4A90E2] shadow-sm">
            <AlertTriangle size={15} />
          </div>
          <div className="space-y-1">
            <div className="text-sm font-semibold text-slate-900">Pro tip</div>
            <p className="text-sm leading-relaxed text-slate-600">
              Double click any row to jump into the thread workspace. The queue is ordered by weighted priority, so legal, SLA,
              churn, and security-heavy threads stay at the top.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
