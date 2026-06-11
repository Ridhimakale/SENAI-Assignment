import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  AlertTriangle,
  Archive,
  Bot,
  CheckCircle2,
  Clock,
  Edit3,
  ExternalLink,
  FileSearch,
  Filter,
  Gavel,
  Inbox,
  LineChart as LineChartIcon,
  Mail,
  Search,
  Send,
  ShieldAlert,
  Tag,
  UserCheck,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const POLL_INTERVAL_MS = Number(import.meta.env.VITE_POLL_INTERVAL_MS || 10000);

const demoThreads = [
  {
    id: 'thread_bob_outage',
    sender: 'bob.jones@enterprise.net',
    company: 'Enterprise Net',
    subject: 'Escalation: SLA Breach + Legal Review',
    category: 'Legal',
    urgency: 'Critical',
    sentiment: 'Negative',
    sentimentScore: -0.86,
    status: 'Escalated',
    requiresHuman: true,
    lastActivity: '2026-01-14T15:20:00Z',
    priority: 100,
    messages: [
      { id: 'msg_057', subject: 'P0 outage', body: 'Our users are down. We need an immediate update.', sentimentScore: -0.62, timestamp: '2026-01-12T09:00:00Z' },
      { id: 'msg_058', subject: 'RCA requested', body: 'Please provide RCA timing and SLA credit details.', sentimentScore: -0.71, timestamp: '2026-01-13T10:30:00Z' },
      { id: 'msg_059', subject: 'Renewal hold', body: 'Our renewal is on hold pending this incident review.', sentimentScore: -0.82, timestamp: '2026-01-14T08:15:00Z' },
      { id: 'msg_060', subject: 'Escalation: SLA Breach + Legal Review', body: 'Our legal team is reviewing the SLA breach. We need RCA and credit obligations confirmed.', sentimentScore: -0.9, timestamp: '2026-01-14T15:20:00Z' },
    ],
    contact: { status: 'VIP', accountValue: 2400000, churnRiskScore: 0.88, vipReason: 'Enterprise Renewal' },
    reasoning: [
      { thought: 'The email references SLA breach and legal review.', action: 'get_thread_history', observation: 'Found four outage-related emails.', next_step: 'Retrieve SLA policy.' },
      { thought: 'Policy grounding is needed.', action: 'search_knowledge_base', observation: 'Retrieved sla_policy.md and escalation_matrix.md.', next_step: 'Check enterprise account context.' },
      { thought: 'Account risk affects escalation priority.', action: 'check_account_status', observation: 'Enterprise tier, renewal on hold.', next_step: 'Flag legal.' },
      { thought: 'Legal review is mandatory.', action: 'flag_for_legal', observation: 'Legal flag proposed.', next_step: 'Draft holding reply.' },
      { thought: 'A reply can be drafted but not auto-sent.', action: 'draft_reply', observation: 'Holding reply cites SLA credit policy.', next_step: 'Escalate to human.' },
      { thought: 'Human review is required.', action: 'escalate_to_human', observation: 'Escalation brief prepared.', next_step: 'Stop and wait for reviewer.' },
    ],
    rag: [
      { source_doc: 'sla_policy.md', score: 0.91, chunk_text: 'P0 incidents require RCA within 24 hours. Credits are applied to future invoices.' },
      { source_doc: 'escalation_matrix.md', score: 0.86, chunk_text: 'Legal threats and SLA disputes require leadership escalation and preserved thread history.' },
    ],
    market: null,
    entities: { monetary_amounts: ['$2.4M'], ticket_ids: [], deadlines: ['within 24 Hours'] },
  },
  {
    id: 'thread_karen_refund',
    sender: 'karen.w@retail-co.com',
    company: 'Retail Co',
    subject: 'Refund ignored, I am posting publicly',
    category: 'Complaint',
    urgency: 'High',
    sentiment: 'Negative',
    sentimentScore: -0.93,
    status: 'Needs Human',
    requiresHuman: true,
    lastActivity: '2026-01-10T12:10:00Z',
    priority: 85,
    messages: [
      { id: 'msg_031', subject: 'Refund request', body: 'I want a refund and nobody has replied.', sentimentScore: -0.56, timestamp: '2026-01-08T10:00:00Z' },
      { id: 'msg_032', subject: 'Still no answer', body: 'This is terrible support. I am considering canceling.', sentimentScore: -0.78, timestamp: '2026-01-09T11:15:00Z' },
      { id: 'msg_033', subject: 'Public review', body: 'I will post publicly on Trustpilot and G2 if this is ignored.', sentimentScore: -0.93, timestamp: '2026-01-10T12:10:00Z' },
    ],
    contact: { status: 'Active', accountValue: 12000, churnRiskScore: 0.94, vipReason: null },
    reasoning: [
      { thought: 'Three negative unanswered emails indicate churn risk.', action: 'get_thread_history', observation: 'Found escalating complaint chain.', next_step: 'Retrieve refund and escalation policies.' },
      { thought: 'Public review threat needs market context.', action: 'scrape_public_sentiment', observation: 'Market Intelligence block prepared from Trustpilot/G2 cache.', next_step: 'Escalate retention case.' },
    ],
    rag: [
      { source_doc: 'refund_policy.md', score: 0.89, chunk_text: 'Public review threats increase priority and should create a retention case.' },
      { source_doc: 'escalation_matrix.md', score: 0.84, chunk_text: 'Public reputation threats route to customer success leadership.' },
    ],
    market: 'Public sentiment is mixed. Common themes include billing confusion and slow support response.',
    entities: { monetary_amounts: [], ticket_ids: [], deadlines: [] },
  },
  {
    id: 'thread_alice_pricing',
    sender: 'alice.smith@greenlight-npo.org',
    company: 'Greenlight NPO',
    subject: 'Pro-rata billing question',
    category: 'Billing',
    urgency: 'Medium',
    sentiment: 'Neutral',
    sentimentScore: 0.05,
    status: 'Pending',
    requiresHuman: false,
    lastActivity: '2026-01-13T16:40:00Z',
    priority: 25,
    messages: [
      { id: 'msg_037', subject: 'Nonprofit pricing', body: 'Do nonprofits receive discounts?', sentimentScore: 0.15, timestamp: '2026-01-01T09:20:00Z' },
      { id: 'msg_041', subject: 'Pro-rata billing question', body: 'If we upgrade, how does the 30% nonprofit discount affect pro-rata billing?', sentimentScore: 0.05, timestamp: '2026-01-13T16:40:00Z' },
    ],
    contact: { status: 'Active', accountValue: 18000, churnRiskScore: 0.22, vipReason: 'Nonprofit Growth' },
    reasoning: [
      { thought: 'The latest email depends on earlier nonprofit pricing context.', action: 'get_thread_history', observation: 'Found prior nonprofit discount discussion.', next_step: 'Retrieve pricing policy.' },
    ],
    rag: [
      { source_doc: 'pricing_policy.md', score: 0.92, chunk_text: 'Qualified nonprofits receive 30% discount on Standard. Upgrades use pro-rata billing.' },
    ],
    market: null,
    entities: { monetary_amounts: ['30%'], ticket_ids: [], deadlines: [] },
  },
  {
    id: 'thread_gdpr_001',
    sender: 'marcus.del@fintech-startup.co',
    company: 'Fintech Startup Co',
    subject: 'Formal GDPR Article 20 request',
    category: 'Compliance',
    urgency: 'High',
    sentiment: 'Neutral',
    sentimentScore: -0.1,
    status: 'Escalated',
    requiresHuman: true,
    lastActivity: '2026-01-11T09:45:00Z',
    priority: 75,
    messages: [
      { id: 'msg_052', subject: 'GDPR Article 20 Request', body: 'This is a formal GDPR Article 20 data portability request.', sentimentScore: -0.1, timestamp: '2026-01-11T09:45:00Z' },
    ],
    contact: { status: 'Active', accountValue: 45000, churnRiskScore: 0.35, vipReason: null },
    reasoning: [
      { thought: 'This is a formal compliance request.', action: 'search_knowledge_base', observation: 'GDPR Article 20 requires compliance review within 30 days.', next_step: 'Create compliance ticket.' },
    ],
    rag: [
      { source_doc: 'compliance_faq.md', score: 0.93, chunk_text: 'Article 20 data portability requests require identity verification and 30 calendar day response window.' },
      { source_doc: 'escalation_matrix.md', score: 0.88, chunk_text: 'GDPR requests route to Compliance Operations and require human review.' },
    ],
    market: null,
    entities: { monetary_amounts: [], ticket_ids: [], deadlines: ['30 calendar days'] },
  },
];

const demoAnalytics = {
  sentimentTrend: [
    { timestamp: 'Jan 1', sentiment_score: -0.2, moving_average: -0.2 },
    { timestamp: 'Jan 4', sentiment_score: -0.4, moving_average: -0.3 },
    { timestamp: 'Jan 8', sentiment_score: -0.7, moving_average: -0.43 },
    { timestamp: 'Jan 12', sentiment_score: -0.3, moving_average: -0.47 },
    { timestamp: 'Jan 14', sentiment_score: 0.1, moving_average: -0.3 },
  ],
  categories: [
    { category: 'Complaint', count: 12 },
    { category: 'Inquiry', count: 18 },
    { category: 'Bug Report', count: 7 },
    { category: 'Compliance', count: 4 },
    { category: 'Legal', count: 3 },
    { category: 'Billing', count: 9 },
  ],
  heatmap: Array.from({ length: 24 }, (_, hour) => ({ hour_of_day: hour, action_count: [0, 0, 1, 0, 0, 1, 2, 4, 8, 10, 7, 6, 5, 8, 9, 11, 7, 5, 3, 2, 1, 0, 0, 0][hour] })),
  atRisk: [
    { sender: 'karen.w@retail-co.com', company: 'Retail Co', churn_risk_score: 0.94, unresolved_threads: 1, oldest_unresolved_hours: 72, consecutive_negative_count: 3, reasons: ['sentiment_deterioration', 'unresolved_threads_over_48h'] },
    { sender: 'bob.jones@enterprise.net', company: 'Enterprise Net', churn_risk_score: 0.88, unresolved_threads: 1, oldest_unresolved_hours: 50, consecutive_negative_count: 2, reasons: ['high_churn_risk_score', 'unresolved_threads_over_48h'] },
  ],
  performance: { total_actions: 31, auto_reply_count: 9, escalation_count: 13, auto_reply_rate: 0.29, escalation_rate: 0.42, average_confidence_score: 0.81 },
};

async function safeFetch(path, fallback) {
  try {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) return fallback;
    const payload = await response.json();
    return payload.data || fallback;
  } catch {
    return fallback;
  }
}

function App() {
  const [activeView, setActiveView] = useState('inbox');
  const [threads, setThreads] = useState(demoThreads);
  const [selectedId, setSelectedId] = useState(demoThreads[0].id);
  const [tab, setTab] = useState('All');
  const [query, setQuery] = useState('');
  const [sortBy, setSortBy] = useState('priority');
  const [analytics, setAnalytics] = useState(demoAnalytics);
  const [lastSync, setLastSync] = useState(new Date());

  useEffect(() => {
    let isMounted = true;
    async function refresh() {
      const sentiment = await safeFetch('/analytics/sentiment-trend', { points: demoAnalytics.sentimentTrend });
      const categories = await safeFetch('/analytics/category-breakdown', { items: demoAnalytics.categories });
      const heatmap = await safeFetch('/analytics/response-heatmap', { points: demoAnalytics.heatmap });
      const atRisk = await safeFetch('/analytics/at-risk-accounts', { accounts: demoAnalytics.atRisk });
      const performance = await safeFetch('/analytics/agent-performance', demoAnalytics.performance);
      if (!isMounted) return;
      setAnalytics({
        sentimentTrend: sentiment.points || demoAnalytics.sentimentTrend,
        categories: categories.items || demoAnalytics.categories,
        heatmap: heatmap.points || demoAnalytics.heatmap,
        atRisk: atRisk.accounts || demoAnalytics.atRisk,
        performance,
      });
      setLastSync(new Date());
    }
    refresh();
    const timer = setInterval(refresh, POLL_INTERVAL_MS);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  const filteredThreads = useMemo(() => {
    const lowered = query.toLowerCase();
    return threads
      .filter((thread) => {
        if (tab === 'Needs Human' && !thread.requiresHuman) return false;
        if (tab === 'Auto-Replied' && thread.status !== 'Replied') return false;
        if (tab === 'Escalated' && thread.status !== 'Escalated') return false;
        if (tab === 'Spam' && thread.category !== 'Spam') return false;
        return !lowered || `${thread.sender} ${thread.subject} ${thread.messages.map((m) => m.body).join(' ')}`.toLowerCase().includes(lowered);
      })
      .sort((a, b) => {
        if (sortBy === 'priority') return b.priority - a.priority;
        if (sortBy === 'sentiment') return a.sentimentScore - b.sentimentScore;
        return new Date(b.lastActivity) - new Date(a.lastActivity);
      });
  }, [threads, tab, query, sortBy]);

  const selectedThread = threads.find((thread) => thread.id === selectedId) || threads[0];

  function bulkSetStatus(status) {
    setThreads((current) => current.map((thread) => ({ ...thread, status })));
  }

  function markSelected(status) {
    setThreads((current) => current.map((thread) => (thread.id === selectedThread.id ? { ...thread, status } : thread)));
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">S</div>
          <div>
            <h1>SenAI Ops</h1>
            <span>CRM Intelligence</span>
          </div>
        </div>
        <nav>
          <button className={activeView === 'inbox' ? 'active' : ''} onClick={() => setActiveView('inbox')}><Inbox size={18} /> Mission Control</button>
          <button className={activeView === 'thread' ? 'active' : ''} onClick={() => setActiveView('thread')}><Mail size={18} /> Thread Workspace</button>
          <button className={activeView === 'analytics' ? 'active' : ''} onClick={() => setActiveView('analytics')}><LineChartIcon size={18} /> Analytics</button>
        </nav>
        <div className="sync-box">
          <Clock size={16} />
          <span>Polling every {Math.round(POLL_INTERVAL_MS / 1000)}s</span>
          <strong>{lastSync.toLocaleTimeString()}</strong>
        </div>
      </aside>

      <section className="workspace">
        <Header activeView={activeView} />
        {activeView === 'inbox' && (
          <MissionControl
            threads={filteredThreads}
            selectedId={selectedId}
            setSelectedId={setSelectedId}
            setActiveView={setActiveView}
            tab={tab}
            setTab={setTab}
            query={query}
            setQuery={setQuery}
            sortBy={sortBy}
            setSortBy={setSortBy}
            bulkSetStatus={bulkSetStatus}
          />
        )}
        {activeView === 'thread' && (
          <ThreadWorkspace thread={selectedThread} markSelected={markSelected} />
        )}
        {activeView === 'analytics' && <AnalyticsDashboard analytics={analytics} />}
      </section>
    </main>
  );
}

function Header({ activeView }) {
  const titles = {
    inbox: 'Mission Control Inbox',
    thread: 'Thread Workspace',
    analytics: 'Analytics Dashboard',
  };
  return (
    <header className="topbar">
      <div>
        <p>AI-powered email operations</p>
        <h2>{titles[activeView]}</h2>
      </div>
      <div className="topbar-actions">
        <span className="status-dot"></span>
        <span>Backend-aware demo mode</span>
      </div>
    </header>
  );
}

function MissionControl({ threads, selectedId, setSelectedId, setActiveView, tab, setTab, query, setQuery, sortBy, setSortBy, bulkSetStatus }) {
  const tabs = ['All', 'Needs Human', 'Auto-Replied', 'Escalated', 'Spam'];
  return (
    <div className="panel-stack">
      <section className="toolbar">
        <div className="search-box"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search subject, body, sender" /></div>
        <label><Filter size={16} /><select value={sortBy} onChange={(event) => setSortBy(event.target.value)}><option value="priority">Priority</option><option value="lastActivity">Last activity</option><option value="sentiment">Most negative</option></select></label>
        <button onClick={() => bulkSetStatus('Spam')}><ShieldAlert size={16} /> Mark Spam</button>
        <button onClick={() => bulkSetStatus('Assigned')}><UserCheck size={16} /> Assign</button>
        <button onClick={() => bulkSetStatus('Archived')}><Archive size={16} /> Archive</button>
      </section>
      <div className="tabs">{tabs.map((item) => <button key={item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)}>{item}</button>)}</div>
      <section className="inbox-list">
        {threads.map((thread) => (
          <article key={thread.id} className={`thread-row ${selectedId === thread.id ? 'selected' : ''}`} onClick={() => setSelectedId(thread.id)}>
            <div className="sender-block">
              <strong>{thread.company}</strong>
              <span>{thread.sender}</span>
            </div>
            <div className="subject-block">
              <button className="link-button" onClick={(event) => { event.stopPropagation(); setActiveView('thread'); }}>{thread.subject}</button>
              <span>{thread.messages.length} messages grouped by sender and thread</span>
            </div>
            <Badge value={thread.sentiment} kind="sentiment" score={thread.sentimentScore} />
            <Badge value={thread.category} />
            <Badge value={thread.urgency} kind="urgency" />
            <div className="last-activity">{new Date(thread.lastActivity).toLocaleString()}</div>
          </article>
        ))}
      </section>
    </div>
  );
}

function ThreadWorkspace({ thread, markSelected }) {
  const latest = thread.messages[thread.messages.length - 1];
  return (
    <div className="thread-grid">
      <section className="email-pane">
        <div className="section-title"><Mail size={18} /> Current Email</div>
        <h3>{latest.subject}</h3>
        <p className="muted">{thread.sender}</p>
        <HighlightedText text={latest.body} entities={thread.entities} />
        {thread.market && <div className="market-inline"><ExternalLink size={16} /> {thread.market}</div>}
        <div className="action-bar">
          <button><CheckCircle2 size={16} /> Approve & Send</button>
          <button><Edit3 size={16} /> Edit Draft</button>
          <button onClick={() => markSelected('Escalated')}><AlertTriangle size={16} /> Escalate</button>
          <button onClick={() => markSelected('Spam')}><ShieldAlert size={16} /> Mark Spam</button>
        </div>
      </section>
      <section className="timeline-pane">
        <div className="section-title"><Clock size={18} /> Thread Timeline</div>
        {thread.messages.map((message) => (
          <div key={message.id} className="timeline-item">
            <span className={message.sentimentScore < -0.5 ? 'sentiment-dot bad' : 'sentiment-dot'}></span>
            <div>
              <strong>{message.subject}</strong>
              <small>{new Date(message.timestamp).toLocaleString()}</small>
              <p>{message.body}</p>
            </div>
          </div>
        ))}
      </section>
      <aside className="context-pane">
        <ContactCard thread={thread} />
        <ReasoningPanel steps={thread.reasoning} />
        <RagPanel chunks={thread.rag} />
      </aside>
    </div>
  );
}

function ContactCard({ thread }) {
  return (
    <section className="context-card">
      <div className="section-title"><UserCheck size={18} /> Contact Profile</div>
      <strong>{thread.company}</strong>
      <p>{thread.sender}</p>
      <div className="metric-row"><span>Status</span><b>{thread.contact.status}</b></div>
      <div className="metric-row"><span>Account Value</span><b>${thread.contact.accountValue.toLocaleString()}</b></div>
      <div className="metric-row"><span>Churn Risk</span><b>{Math.round(thread.contact.churnRiskScore * 100)}%</b></div>
      {thread.contact.vipReason && <div className="note"><Tag size={14} /> {thread.contact.vipReason}</div>}
    </section>
  );
}

function ReasoningPanel({ steps }) {
  return (
    <details className="context-card" open>
      <summary><Bot size={18} /> Agent Reasoning</summary>
      {steps.map((step, index) => (
        <div className="reason-step" key={`${step.action}-${index}`}>
          <strong>Thought</strong><p>{step.thought}</p>
          <strong>Action</strong><p>{step.action}</p>
          <strong>Observation</strong><p>{step.observation}</p>
          <strong>Next</strong><p>{step.next_step}</p>
        </div>
      ))}
    </details>
  );
}

function RagPanel({ chunks }) {
  return (
    <details className="context-card" open>
      <summary><FileSearch size={18} /> RAG Context</summary>
      {chunks.map((chunk) => (
        <div className="rag-row" key={`${chunk.source_doc}-${chunk.score}`}>
          <div><strong>{chunk.source_doc}</strong><span>{Math.round(chunk.score * 100)}%</span></div>
          <p>{chunk.chunk_text}</p>
        </div>
      ))}
    </details>
  );
}

function AnalyticsDashboard({ analytics }) {
  const categoryColors = ['#1f7a8c', '#bf7d30', '#435e53', '#9a4d4d', '#3e5f8a', '#6f6a3a'];
  return (
    <div className="analytics-grid">
      <section className="chart-panel wide">
        <div className="section-title"><LineChartIcon size={18} /> Sentiment Trend</div>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={analytics.sentimentTrend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis domain={[-1, 1]} />
            <Tooltip />
            <Line type="monotone" dataKey="sentiment_score" stroke="#9a4d4d" strokeWidth={2} />
            <Line type="monotone" dataKey="moving_average" stroke="#1f7a8c" strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </section>
      <section className="chart-panel">
        <div className="section-title"><Tag size={18} /> Category Distribution</div>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie data={analytics.categories} dataKey="count" nameKey="category" outerRadius={88}>
              {analytics.categories.map((item, index) => <Cell key={item.category} fill={categoryColors[index % categoryColors.length]} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </section>
      <section className="chart-panel">
        <div className="section-title"><Clock size={18} /> Response Heatmap</div>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={analytics.heatmap}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour_of_day" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="action_count" fill="#1f7a8c" />
          </BarChart>
        </ResponsiveContainer>
      </section>
      <section className="chart-panel">
        <div className="section-title"><AlertTriangle size={18} /> At-Risk Accounts</div>
        {analytics.atRisk.map((account) => (
          <div className="risk-row" key={account.sender}>
            <strong>{account.company}</strong>
            <span>{account.sender}</span>
            <div className="metric-row"><span>Risk</span><b>{Math.round(account.churn_risk_score * 100)}%</b></div>
            <p>{account.reasons.join(', ')}</p>
          </div>
        ))}
      </section>
      <section className="chart-panel">
        <div className="section-title"><Bot size={18} /> Agent Performance</div>
        <div className="kpi-grid">
          <Kpi label="Auto-reply rate" value={`${Math.round(analytics.performance.auto_reply_rate * 100)}%`} />
          <Kpi label="Escalation rate" value={`${Math.round(analytics.performance.escalation_rate * 100)}%`} />
          <Kpi label="Avg confidence" value={`${Math.round(analytics.performance.average_confidence_score * 100)}%`} />
          <Kpi label="Total actions" value={analytics.performance.total_actions} />
        </div>
        <ResponsiveContainer width="100%" height={120}>
          <AreaChart data={[analytics.performance]}>
            <Area dataKey="auto_reply_rate" fill="#1f7a8c" stroke="#1f7a8c" />
            <Area dataKey="escalation_rate" fill="#bf7d30" stroke="#bf7d30" />
          </AreaChart>
        </ResponsiveContainer>
      </section>
    </div>
  );
}

function Kpi({ label, value }) {
  return <div className="kpi"><span>{label}</span><strong>{value}</strong></div>;
}

function Badge({ value, kind, score }) {
  let className = 'badge';
  if (kind === 'urgency') className += ` urgency-${value.toLowerCase()}`;
  if (kind === 'sentiment') className += score < -0.5 ? ' sentiment-bad' : score > 0.3 ? ' sentiment-good' : ' sentiment-mid';
  return <span className={className}>{value}</span>;
}

function HighlightedText({ text, entities }) {
  const tokens = [...(entities.monetary_amounts || []), ...(entities.ticket_ids || []), ...(entities.deadlines || [])].filter(Boolean);
  if (!tokens.length) return <p className="email-body">{text}</p>;
  let parts = [text];
  tokens.forEach((token) => {
    parts = parts.flatMap((part) => typeof part === 'string' ? part.split(token).flatMap((piece, index, array) => index < array.length - 1 ? [piece, <mark key={`${token}-${index}`}>{token}</mark>] : [piece]) : [part]);
  });
  return <p className="email-body">{parts}</p>;
}

createRoot(document.getElementById('root')).render(<App />);
