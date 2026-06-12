import * as React from 'react';
import { useStore } from '../../store';
import { useThreads, useSendManualReply, useUpdateContactStatus, useReputation } from '../../services/queries';
import { api } from '../../services/api';
import { ContactProfile } from '../../types';
import {
  Bot,
  BookOpen,
  Brain,
  Clock3,
  Compass,
  Archive,
  FileCog,
  FileText,
  Globe,
  Loader2,
  Mail,
  MessageSquare,
  Send,
  Sparkles,
  User,
  ChevronRight,
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Select } from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { formatCurrency, formatPercentage } from '../../lib/utils';

type InsightState = {
  ragResults: any[];
  reasoningTrace: any[];
};

const emptyContact: ContactProfile = {
  status: 'Active',
  accountValue: 0,
  churnRiskScore: 0,
  vipReason: null,
  openThreads: 0,
  openTicketCount: 0,
  subscriptionTier: null,
  renewalStatus: null,
};

function summarizeSnippet(text: string, maxLength = 180) {
  const cleaned = String(text || '')
    .replace(/\s+/g, ' ')
    .replace(/\*\s*/g, ' ')
    .trim();

  if (!cleaned) return '';

  const sentenceMatch = cleaned.match(/^(.+?[.!?])(\s|$)/);
  const firstSentence = sentenceMatch?.[1] || cleaned;
  if (firstSentence.length <= maxLength) {
    return firstSentence;
  }

  return `${firstSentence.slice(0, maxLength - 1).trimEnd()}…`;
}

export function ThreadWorkspace() {
  const { selectedId, setSelectedId, draftBodies, updateDraftBody, setActionMessage, connectionState } = useStore();
  const { data: threads, isLoading } = useThreads();
  const sendReplyMutation = useSendManualReply();
  const updateContactMutation = useUpdateContactStatus();

  const thread = React.useMemo(() => {
    if (!threads?.length) return null;
    return threads.find((t) => t.id === selectedId) || threads[0];
  }, [threads, selectedId]);

  const messages = React.useMemo(() => {
    return Array.isArray(thread?.messages) ? thread!.messages : [];
  }, [thread]);

  const contact = thread?.contact || emptyContact;
  const companyName = thread?.company || 'Unknown Account';
  const senderEmail = thread?.sender || 'unknown@example.com';

  const { data: reputationData, isLoading: isReputationLoading } = useReputation(thread?.company || null);

  const [insight, setInsight] = React.useState<InsightState>({ ragResults: [], reasoningTrace: [] });
  const [isInsightLoading, setIsInsightLoading] = React.useState(false);
  const [isEditingContact, setIsEditingContact] = React.useState(false);
  const [contactStatus, setContactStatus] = React.useState(contact.status);
  const [accountValue, setAccountValue] = React.useState(contact.accountValue);
  const [churnRisk, setChurnRisk] = React.useState(contact.churnRiskScore);
  const [vipReason, setVipReason] = React.useState(contact.vipReason || '');
  const [draftText, setDraftText] = React.useState('');
  const [draftEditorOpen, setDraftEditorOpen] = React.useState(false);
  const [draftEditorText, setDraftEditorText] = React.useState('');
  const [threadStatus, setThreadStatus] = React.useState(thread?.status || 'Open');
  const [toastMessage, setToastMessage] = React.useState<string | null>(null);
  const [activeCopilotTab, setActiveCopilotTab] = React.useState<'reasoning' | 'rag' | 'market'>('reasoning');

  React.useEffect(() => {
    if (!thread) return;

    setContactStatus(contact.status);
    setAccountValue(contact.accountValue);
    setChurnRisk(contact.churnRiskScore);
    setVipReason(contact.vipReason || '');
    setThreadStatus(thread.status || 'Open');

    const latest = messages[messages.length - 1];
    const initialDraft =
      draftBodies[thread.id] ||
        `Hi ${companyName},\n\nThanks for reaching out. We are reviewing your ${thread.category.toLowerCase()} request and will respond shortly.\n\nBest,\nSENAI Ops`
    setDraftText(initialDraft);
    setDraftEditorText(initialDraft);

    async function loadInsights() {
      setIsInsightLoading(true);
      const queryText = [thread.subject, latest?.body, thread.sender].filter(Boolean).join(' ').slice(0, 3500);
      try {
        const [ragResults, agentTrace] = await Promise.all([
          api.searchKnowledgeBase(queryText),
          latest?.emailId ? api.dryRunAgent(latest.emailId) : Promise.resolve(null),
        ]);
        setInsight({
          ragResults: Array.isArray(ragResults) && ragResults.length ? ragResults : (thread.rag || []),
          reasoningTrace: Array.isArray(agentTrace?.reasoning_trace) ? agentTrace.reasoning_trace : thread.reasoning || [],
        });
      } catch {
        setInsight({
          ragResults: thread.rag || [],
          reasoningTrace: thread.reasoning || [],
        });
      } finally {
        setIsInsightLoading(false);
      }
    }

    loadInsights();
  }, [thread, contact.status, contact.accountValue, contact.churnRiskScore, contact.vipReason, draftBodies, messages, companyName]);

  React.useEffect(() => {
    if (!toastMessage) return;
    const timer = window.setTimeout(() => setToastMessage(null), 2200);
    return () => window.clearTimeout(timer);
  }, [toastMessage]);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center gap-2 text-sm text-slate-500">
        <Loader2 size={16} className="animate-spin text-slate-400" />
        <span>Loading thread workspace context...</span>
      </div>
    );
  }

  if (!thread) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        <Mail size={32} className="mx-auto text-slate-300" />
        <p className="mt-3">No thread selected. Please select a thread from the Inbox.</p>
      </div>
    );
  }

  const latestMessage = messages[messages.length - 1];
  const summarySteps = insight.reasoningTrace?.length ? insight.reasoningTrace : thread.reasoning || [];
  const threadSummary =
    thread.executiveSummary ||
    (messages.length >= 5
      ? `This thread has ${messages.length} messages and shows a sustained escalation pattern. The latest update focuses on ${latestMessage?.subject || 'the current issue'}, so the conversation should be handled with care. Because the thread is long-running, policy-aware follow-up and close tracking are recommended.`
      : null);

  const handleSaveDraft = () => {
    updateDraftBody(thread.id, draftText);
    setActionMessage('Draft saved locally.');
  };

  const openDraftEditor = () => {
    setDraftEditorText(draftText);
    setDraftEditorOpen(true);
  };

  const closeDraftEditor = () => {
    setDraftEditorOpen(false);
  };

  const saveDraftEditor = () => {
    setDraftText(draftEditorText);
    updateDraftBody(thread.id, draftEditorText);
    setDraftEditorOpen(false);
    setActionMessage('Draft updated from popout editor.');
  };

  const handleGenerateDraft = () => {
    const emailId = latestMessage?.emailId ?? (typeof latestMessage?.id === 'number' ? latestMessage.id : Number(latestMessage?.id));
    const threadIntent = thread.category.toLowerCase();
    const demoDraft = `Hi ${companyName},\n\nThanks for reaching out. We reviewed the current thread context and are treating this as a ${threadIntent} case.\n\n${threadSummary ? `In short: ${threadSummary}\n\n` : ''}We are keeping this reply aligned with the conversation history and the relevant policy context. Please let us know if you'd like us to move this to a human reviewer.\n\nBest,\nSENAI Ops`;

    if (!Number.isFinite(emailId) || emailId <= 0) {
      setDraftText(demoDraft);
      setDraftEditorText(demoDraft);
      setActionMessage('Demo draft generated from thread context.');
      return;
    }

    setIsInsightLoading(true);
    api
      .generateDraft(emailId)
      .then((result) => {
        const preview =
          result?.draft ||
          demoDraft;

        setDraftText(preview);
        setDraftEditorText(preview);
        setActionMessage('AI draft generated from backend agent.');
      })
      .catch(() => {
        setDraftText(demoDraft);
        setDraftEditorText(demoDraft);
        setActionMessage('Fallback draft generated locally.');
      })
      .finally(() => {
        setIsInsightLoading(false);
      });
  };

  const handleInsertKnowledge = () => {
    const source = insight.ragResults[0] || thread.rag?.[0];
    if (!source) {
      setToastMessage('No knowledge base snippet available');
      setActionMessage('No knowledge base snippet available.');
      return;
    }
    setDraftText((prev) => `${prev}\n\n[KB: ${source.source_doc}] ${source.chunk_text}`);
    setDraftEditorText((prev) => `${prev}\n\n[KB: ${source.source_doc}] ${source.chunk_text}`);
    setToastMessage('Knowledge base snippet inserted');
    setActionMessage('Knowledge base snippet inserted.');
  };

  const handleSendReply = () => {
    const emailId = latestMessage?.emailId || 1;
    sendReplyMutation.mutate(
      { emailId, body: draftText, sender: 'dashboard' },
      {
        onSuccess: () => {
          setToastMessage('Reply sent successfully');
          setActionMessage('Reply sent successfully.');
        },
      }
    );
  };

  const handleArchiveThread = () => {
    setThreadStatus('Archived');
    setToastMessage('Thread archived');
    setActionMessage('Thread archived locally.');
  };

  const handleSaveContact = () => {
    updateContactMutation.mutate(
      {
        email: thread.sender,
        updates: {
          status: contactStatus,
          accountValue,
          churnRiskScore: churnRisk,
          vipReason: vipReason || null,
        },
      },
      {
        onSuccess: () => {
          setIsEditingContact(false);
          setActionMessage('Customer profile updated.');
        },
      }
    );
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">
          <Sparkles size={13} className="text-[#4A90E2]" />
          <span>Thread Workspace</span>
        </div>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-[2rem] font-bold tracking-tight text-slate-900">{thread.subject}</h2>
            <p className="mt-1 text-sm text-slate-500">Customer context, AI reasoning, RAG sources, and response controls in one view.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-3 py-1 text-xs font-semibold">
              Priority P{thread.priority}
            </Badge>
            <Badge className="rounded-full bg-[#4A90E2] px-3 py-1 text-xs font-semibold text-white">{thread.urgency}</Badge>
            <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-3 py-1 text-xs font-semibold">
              {threadStatus}
            </Badge>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)_400px]">
        <div className="space-y-6">
          <Card className="border-slate-200 bg-white">
            <CardHeader className="border-b border-slate-100 p-5">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-slate-900">
                <User size={16} className="text-slate-400" />
                Customer Profile
              </CardTitle>
              <CardDescription className="text-sm">Account context and risk signals.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#4A90E2]/10 text-sm font-bold text-[#4A90E2]">
                  {companyName
                    .split(' ')
                    .map((part) => part[0])
                    .join('')
                    .slice(0, 2)
                    .toUpperCase()}
                </div>
                <div>
                  <div className="text-sm font-bold text-slate-900">{companyName}</div>
                  <div className="text-xs text-slate-500">{senderEmail}</div>
                </div>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                {[
                  ['Status', contact.status],
                  ['Contract Value', formatCurrency(contact.accountValue)],
                  ['Churn Risk', formatPercentage(contact.churnRiskScore)],
                  ['Open Threads', contact.openThreads ?? 0],
                  ['Open Tickets', contact.openTicketCount ?? 0],
                  ['Renewal Status', contact.renewalStatus ?? 'Unknown'],
                ].map(([label, value]) => (
                  <div key={label} className="flex items-center justify-between py-2 text-sm">
                    <span className="text-slate-500">{label}</span>
                    <span className="font-semibold text-slate-900">{value as React.ReactNode}</span>
                  </div>
                ))}
              </div>

              <Button
                variant="outline"
                size="sm"
                className="h-11 w-full rounded-xl border-slate-200 text-sm text-slate-700"
                onClick={() => setIsEditingContact((prev) => !prev)}
              >
                <FileCog size={14} />
                <span>{isEditingContact ? 'Cancel edit' : 'Update Profile'}</span>
              </Button>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white">
            <CardHeader className="border-b border-slate-100 p-5">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-slate-900">
                <Clock3 size={16} className="text-slate-400" />
                Conversation Summary
              </CardTitle>
              <CardDescription className="text-sm">AI-generated summary for quick review.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-5 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Customer intent</span>
                <span className="font-semibold text-slate-900">{thread.category}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Risk level</span>
                <span className="font-semibold text-slate-900">{thread.urgency}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Recommended action</span>
                  <span className="font-semibold text-slate-900">{thread.requiresHuman ? 'Escalate' : 'Auto respond'}</span>
                </div>
              {threadSummary && (
                <div className="rounded-2xl border border-[#CFE0FF] bg-[#F4F8FF] p-3 text-sm leading-6 text-slate-700">
                  <div className="mb-1 text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-[#4A90E2]">
                    Executive Summary
                  </div>
                  {threadSummary}
                </div>
              )}
              </CardContent>
            </Card>
        </div>

        <div className="space-y-6">
          <Card className="border-slate-200 bg-white">
            <CardHeader className="border-b border-slate-100 p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-base font-semibold text-slate-900">Conversation Timeline</CardTitle>
                  <CardDescription className="text-sm">Chronological thread history with sentiment markers.</CardDescription>
                </div>
                <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-3 py-1 text-xs font-semibold">
                  {messages.length} messages
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 p-5">
              {messages.map((message, index) => (
                <div key={message.id} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 shadow-sm">
                  <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-2">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-slate-500 shadow-sm">
                        <Mail size={14} />
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-slate-900">{message.subject}</div>
                        <div className="text-xs text-slate-500">Message #{index + 1}</div>
                      </div>
                    </div>
                    <div className="text-xs font-medium text-slate-500">
                      {new Date(message.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{message.body}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white">
            <CardHeader className="border-b border-slate-100 p-5">
              <CardTitle className="text-base font-semibold text-slate-900">Reply Composer</CardTitle>
              <CardDescription className="text-sm">Draft a grounded response with policy support.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 p-5">
              {threadSummary && (
                <div className="rounded-2xl border border-[#CFE0FF] bg-[#F4F8FF] p-3 text-sm leading-6 text-slate-700">
                  <div className="mb-1 text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-[#4A90E2]">
                    Thread Summary
                  </div>
                  {threadSummary}
                </div>
              )}
              <div className="flex flex-wrap items-center gap-2">
                <Button variant="outline" size="sm" className="h-10 rounded-xl border-slate-200 px-3 text-sm" onClick={handleGenerateDraft}>
                  <Brain size={14} />
                  <span>Generate Draft</span>
                </Button>
                <Button variant="outline" size="sm" className="h-10 rounded-xl border-slate-200 px-3 text-sm" onClick={handleInsertKnowledge}>
                  <BookOpen size={14} />
                  <span>Insert KB</span>
                </Button>
                <Button variant="outline" size="sm" className="h-10 rounded-xl border-slate-200 px-3 text-sm" onClick={openDraftEditor}>
                  <FileText size={14} />
                  <span>Edit Draft</span>
                </Button>
                <Button variant="default" size="sm" className="h-10 rounded-xl bg-[#4A90E2] px-3 text-sm text-white hover:bg-[#3f82cf]" onClick={handleSendReply}>
                  <Send size={14} />
                  <span>Approve & Send</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-10 rounded-xl border-slate-200 px-3 text-sm"
                  onClick={handleArchiveThread}
                >
                  <Archive size={14} />
                  <span>Archive</span>
                </Button>
              </div>

              <textarea
                value={draftText}
                readOnly
                className="min-h-[220px] w-full rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-sm leading-6 text-slate-800 shadow-sm outline-none focus:border-[#4A90E2]"
                placeholder="Write your reply here..."
              />

              <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
                <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-3 py-1 text-xs font-semibold">
                  Draft autosaved locally
                </Badge>
                {connectionState === 'demo' && (
                  <Badge variant="warning" className="rounded-full px-3 py-1 text-xs font-semibold">
                    Demo mode auto-sends
                  </Badge>
                )}
              </div>

              {toastMessage && (
                <div className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm">
                  {toastMessage}
                </div>
              )}

              {isEditingContact && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Status</label>
                      <Select value={contactStatus} onChange={(e) => setContactStatus(e.target.value)}>
                        <option value="Active">Active</option>
                        <option value="VIP">VIP</option>
                        <option value="Churn Risk">Churn Risk</option>
                        <option value="Blocked">Blocked</option>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Account Value</label>
                      <Input type="number" value={accountValue} onChange={(e) => setAccountValue(Number(e.target.value))} />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Churn Risk</label>
                      <Input type="number" step="0.05" value={churnRisk} onChange={(e) => setChurnRisk(Number(e.target.value))} />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">VIP Reason</label>
                      <Input type="text" value={vipReason} onChange={(e) => setVipReason(e.target.value)} />
                    </div>
                  </div>
                  <div className="mt-4 flex justify-end gap-2">
                    <Button variant="outline" size="sm" className="h-10 rounded-xl border-slate-200 px-4 text-sm" onClick={() => setIsEditingContact(false)}>
                      Cancel
                    </Button>
                    <Button variant="default" size="sm" className="h-10 rounded-xl bg-[#4A90E2] px-4 text-sm text-white hover:bg-[#3f82cf]" onClick={handleSaveContact}>
                      {updateContactMutation.isPending ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="border-slate-200 bg-white">
            <CardHeader className="border-b border-slate-100 p-5">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-slate-900">
                <Bot size={16} className="text-[#4A90E2]" />
                AI Copilot Panel
              </CardTitle>
              <CardDescription className="text-sm">Reasoning, retrieved policies, and market intelligence.</CardDescription>
            </CardHeader>
            <CardContent className="p-5">
              <Tabs value={activeCopilotTab} onValueChange={(value) => setActiveCopilotTab(value as typeof activeCopilotTab)} className="space-y-3">
                <TabsList className="grid grid-cols-3">
                  <TabsTrigger value="reasoning">Thought</TabsTrigger>
                  <TabsTrigger value="rag">RAG</TabsTrigger>
                  <TabsTrigger value="market">Market</TabsTrigger>
                </TabsList>
                <TabsContent value="reasoning" className="space-y-3">
                  {isInsightLoading ? (
                    <div className="flex h-40 items-center justify-center gap-2 text-sm text-slate-500">
                      <Loader2 size={15} className="animate-spin text-slate-400" />
                      <span>Analyzing reasoning graph...</span>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {summarySteps.map((step: any, index: number) => (
                        <details key={index} className="group rounded-2xl border border-slate-200 bg-white shadow-sm" open={index === 0}>
                          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 p-4">
                            <div className="flex items-center gap-2">
                              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#EAF2FF] text-[#4A90E2]">
                                <ChevronRight size={14} className="rotate-90" />
                              </div>
                              <div>
                                <div className="text-sm font-semibold text-slate-900">Step {index + 1}</div>
                                <div className="text-xs text-slate-500">{step.action || 'Thought'}</div>
                              </div>
                            </div>
                            <ChevronRight size={14} className="text-slate-400 transition-transform group-open:rotate-90" />
                          </summary>
                          <div className="border-t border-slate-100 px-4 pb-4 text-sm text-slate-700">
                            <div className="mt-3 space-y-3">
                              <div>
                                <div className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-slate-400">Thought</div>
                                <p className="mt-1 leading-6">{step.thought || step}</p>
                              </div>
                              {step.observation && (
                                <div>
                                  <div className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-slate-400">Observation</div>
                                  <p className="mt-1 leading-6 text-slate-600">{step.observation}</p>
                                </div>
                              )}
                              {step.next_step && (
                                <div>
                                  <div className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-slate-400">Next step</div>
                                  <p className="mt-1 leading-6 text-slate-600">{step.next_step}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        </details>
                      ))}
                    </div>
                  )}
                </TabsContent>
                <TabsContent value="rag" className="space-y-3">
                  {insight.ragResults.length ? (
                    insight.ragResults.map((source: any, i: number) => (
                      <Card key={i} className="border-slate-200 bg-white">
                        <CardContent className="space-y-3 p-4">
                          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                            <div className="flex items-center gap-2">
                              <BookOpen size={14} className="text-slate-400" />
                              <span className="text-sm font-semibold text-slate-900">{source.source_doc || `document_${i}`}</span>
                            </div>
                            <Badge variant="outline" className="rounded-full border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold">
                              Match {formatPercentage(source.score || 0.8)}
                            </Badge>
                          </div>
                          <p className="rounded-2xl border border-slate-100 bg-slate-50/70 p-3 text-sm leading-6 text-slate-600 line-clamp-4">
                            {summarizeSnippet(source.chunk_text)}
                          </p>
                        </CardContent>
                      </Card>
                    ))
                  ) : (
                    <div className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
                      No knowledge base chunks matched the thread context.
                    </div>
                  )}
                </TabsContent>
                <TabsContent value="market" className="space-y-3">
                  {isReputationLoading ? (
                    <div className="flex h-40 items-center justify-center gap-2 text-sm text-slate-500">
                      <Loader2 size={15} className="animate-spin text-slate-400" />
                      <span>Scraping market intelligence...</span>
                    </div>
                  ) : reputationData ? (
                    <Card className="border-slate-200 bg-white">
                      <CardHeader className="border-b border-slate-100 p-4">
                        <CardTitle className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                          <Globe size={14} className="text-[#4A90E2]" />
                          Public Sentiment
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3 p-4 text-sm text-slate-600">
                        <p className="leading-6">{reputationData.summary || reputationData}</p>
                        {reputationData.market_intelligence_block && (
                          <div className="rounded-2xl border border-red-100 bg-red-50/40 p-3 text-sm text-red-700">
                            {reputationData.market_intelligence_block}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
                      No market intelligence available for this thread.
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white">
            <CardHeader className="border-b border-slate-100 p-5">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-slate-900">
                <Compass size={16} className="text-slate-400" />
                Risk & Compliance
              </CardTitle>
              <CardDescription className="text-sm">Safety checks for this thread.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-5 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Human review required</span>
                <span className="font-semibold text-slate-900">{thread.requiresHuman ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Compliance flags</span>
                <span className="font-semibold text-slate-900">{thread.category === 'Compliance' || thread.category === 'Legal' ? 'Active' : 'None'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Thread count</span>
                <span className="font-semibold text-slate-900">{messages.length}</span>
              </div>
              <div className="rounded-2xl bg-slate-50 p-3 text-xs leading-6 text-slate-600">
                {thread.requiresHuman
                  ? 'This thread is gated for human review or policy-aware escalation before automatic reply.'
                  : 'This thread is currently safe to automate subject to policy checks and response drafting.'}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {draftEditorOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4">
          <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-5 shadow-2xl">
            <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <div className="text-sm font-semibold text-slate-900">Edit Draft</div>
                <div className="text-xs text-slate-500">Make a quick change before sending.</div>
              </div>
              <Button variant="ghost" size="sm" className="h-9 rounded-xl px-3 text-sm" onClick={closeDraftEditor}>
                Close
              </Button>
            </div>
            <textarea
              value={draftEditorText}
              onChange={(e) => setDraftEditorText(e.target.value)}
              className="mt-4 min-h-[180px] w-full rounded-2xl border border-slate-200 bg-slate-50/80 p-4 text-sm leading-6 text-slate-800 outline-none focus:border-[#4A90E2]"
              placeholder="Edit the draft here..."
            />
            <div className="mt-4 flex justify-center">
              <Button
                variant="default"
                size="sm"
                className="h-11 rounded-xl bg-[#4A90E2] px-6 text-sm text-white hover:bg-[#3f82cf]"
                onClick={saveDraftEditor}
              >
                Done
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
