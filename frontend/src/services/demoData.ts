import { Thread, AnalyticsData, DashboardStats } from '../types';

export const DEMO_THREADS: Thread[] = [
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

export const DEMO_ANALYTICS: AnalyticsData = {
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
  heatmap: Array.from({ length: 24 }, (_, hour) => ({
    hour_of_day: hour,
    action_count: [0, 0, 1, 0, 0, 1, 2, 4, 8, 10, 7, 6, 5, 8, 9, 11, 7, 5, 3, 2, 1, 0, 0, 0][hour],
  })),
  atRisk: [
    { sender: 'karen.w@retail-co.com', company: 'Retail Co', churn_risk_score: 0.94, unresolved_threads: 1, oldest_unresolved_hours: 72, consecutive_negative_count: 3, reasons: ['sentiment_deterioration', 'unresolved_threads_over_48h'] },
    { sender: 'bob.jones@enterprise.net', company: 'Enterprise Net', churn_risk_score: 0.88, unresolved_threads: 1, oldest_unresolved_hours: 50, consecutive_negative_count: 2, reasons: ['high_churn_risk_score', 'unresolved_threads_over_48h'] },
  ],
  performance: {
    total_actions: 31,
    auto_reply_count: 9,
    escalation_count: 13,
    auto_reply_rate: 0.29,
    escalation_rate: 0.42,
    average_confidence_score: 0.81,
  },
};

export const DEMO_STATS: DashboardStats = {
  pending: 2,
  replied: 1,
  escalated: 2,
  critical: 1,
  spam: 0,
  needs_human: 3,
};

export const CONTACT_DIRECTORY = [
  { email: 'bob.jones@enterprise.net', label: 'Bob Jones', company: 'Enterprise Net', theme: 'SLA escalation' },
  { email: 'alice.smith@greenlight-npo.org', label: 'Alice Smith', company: 'Greenlight NPO', theme: 'Pricing and pro-rata' },
  { email: 'karen.w@retail-co.com', label: 'Karen W', company: 'Retail Co', theme: 'Refund and churn risk' },
  { email: 'marcus.del@fintech-startup.co', label: 'Marcus Del', company: 'Fintech Startup Co', theme: 'GDPR request' },
];

export const DEMO_JOURNEYS = [
  { id: 'thread_bob_outage', label: 'Bob SLA', view: 'thread' as const, note: 'SLA breach + legal review' },
  { id: 'thread_karen_refund', label: 'Karen Churn', view: 'thread' as const, note: 'Refund + public review threat' },
  { id: 'thread_gdpr_001', label: 'GDPR', view: 'thread' as const, note: 'Article 20 compliance request' },
  { id: 'thread_alice_pricing', label: 'Alice Pricing', view: 'thread' as const, note: 'Nonprofit pricing + pro-rata' },
];
