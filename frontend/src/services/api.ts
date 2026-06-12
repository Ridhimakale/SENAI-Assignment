import {
  Thread,
  AnalyticsData,
  DashboardStats,
  SimulationRequest,
  SimulationResponse,
  ContactProfile,
  RagSource,
  AgentRunResponse,
  DraftGenerationResponse,
} from '../types';
import { DEMO_THREADS, DEMO_ANALYTICS, DEMO_STATS, CONTACT_DIRECTORY } from './demoData';
import { useStore } from '../store';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function safeRequest<T>(
  path: string,
  options?: RequestInit,
  fallback?: T
): Promise<T> {
  const store = useStore.getState();
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
    });

    if (!response.ok) {
      console.warn(`Request to ${path} returned status ${response.status}`);
      return fallback as T;
    }

    const json = await response.json();
    // API responses are wrapped in ApiResponse: { success: boolean, data: T, error?: any }
    return (json.data !== undefined ? json.data : json) as T;
  } catch (error) {
    console.warn(`Network/Request error on ${path}:`, error);
    return fallback as T;
  }
}

export const api = {
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
      return response.ok;
    } catch {
      return false;
    }
  },

  async fetchDashboardStats(): Promise<DashboardStats> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return DEMO_STATS;
    return safeRequest<DashboardStats>('/dashboard/stats', undefined, DEMO_STATS);
  },

  async fetchAllThreads(): Promise<Thread[]> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return DEMO_THREADS;

    try {
      // Fetch threads for all known contacts in parallel
      const nested = await Promise.all(
        CONTACT_DIRECTORY.map(async (contact) => {
          const payload = await safeRequest<{ threads?: any[]; contact?: any } | null>(
            `/threads/${encodeURIComponent(contact.email)}`,
            undefined,
            null
          );

          if (!payload || !payload.threads || payload.threads.length === 0) {
            return DEMO_THREADS.filter((t) => t.sender === contact.email);
          }

          const contactProfile = payload.contact || { email: contact.email, company: contact.company };
          return payload.threads.map((thread) =>
            normalizeThreadRow(thread, {
              ...contactProfile,
              email: contact.email,
              company: contactProfile.company || contact.company,
            })
          );
        })
      );
      const threads = nested.flat().filter(Boolean) as Thread[];
      return threads.length ? mergeThreadRows(DEMO_THREADS, threads) : DEMO_THREADS;
    } catch (e) {
      console.error('Failed to fetch threads:', e);
      return DEMO_THREADS;
    }
  },

  async sendManualReply(emailId: number, body: string, sender: string): Promise<boolean> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return true;

    const res = await safeRequest<any>(
      `/respond/${emailId}`,
      {
        method: 'POST',
        body: JSON.stringify({ body, sender }),
      },
      null
    );
    return res !== null;
  },

  async updateDraft(draftId: number, proposedContent: string): Promise<boolean> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return true;

    const res = await safeRequest<any>(
      `/drafts/${draftId}`,
      {
        method: 'PATCH',
        body: JSON.stringify({ proposed_content: proposedContent }),
      },
      null
    );
    return res !== null;
  },

  async approveDraft(draftId: number, approvedBy: string): Promise<boolean> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return true;

    const res = await safeRequest<any>(
      `/drafts/${draftId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify({ approved_by: approvedBy }),
      },
      null
    );
    return res !== null;
  },

  async fetchContactProfile(email: string): Promise<ContactProfile | null> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) {
      const match = DEMO_THREADS.find((t) => t.sender === email);
      return match ? match.contact : null;
    }
    return safeRequest<ContactProfile | null>(`/contacts/${encodeURIComponent(email)}`, undefined, null);
  },

  async updateContactStatus(email: string, updates: Partial<ContactProfile>): Promise<boolean> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return true;

    // Convert keys to snake_case if expected by FastAPI schema
    const snakeCaseUpdates = {
      status: updates.status,
      is_vip: updates.status === 'VIP',
      vip_reason: updates.vipReason,
      account_value: updates.accountValue,
      churn_risk_score: updates.churnRiskScore,
    };

    const res = await safeRequest<any>(
      `/contacts/${encodeURIComponent(email)}/status`,
      {
        method: 'PATCH',
        body: JSON.stringify(snakeCaseUpdates),
      },
      null
    );
    return res !== null;
  },

  async fetchAnalytics(): Promise<AnalyticsData> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return DEMO_ANALYTICS;

    const [sentiment, categories, heatmap, atRisk, performance] = await Promise.all([
      safeRequest<any>('/analytics/sentiment-trend?days=30', undefined, { points: DEMO_ANALYTICS.sentimentTrend }),
      safeRequest<any>('/analytics/category-breakdown', undefined, { items: DEMO_ANALYTICS.categories }),
      safeRequest<any>('/analytics/response-heatmap', undefined, { points: DEMO_ANALYTICS.heatmap }),
      safeRequest<any>('/analytics/at-risk-accounts', undefined, { accounts: DEMO_ANALYTICS.atRisk }),
      safeRequest<any>('/analytics/agent-performance', undefined, DEMO_ANALYTICS.performance),
    ]);

    const liveSentimentTrend = sentiment?.points || [];
    const liveCategories = categories?.items || [];
    const liveHeatmap = heatmap?.points || [];
    const liveAtRisk = atRisk?.accounts || [];
    const livePerformance = performance || null;
    const liveHeatmapTotal = liveHeatmap.reduce((sum, point) => sum + Number(point.action_count || 0), 0);

    const shouldFallbackSentiment = liveSentimentTrend.length === 0;
    const shouldFallbackCategories = liveCategories.length === 0;
    const shouldFallbackHeatmap = liveHeatmap.length === 0 || liveHeatmapTotal === 0;
    const shouldFallbackPerformance =
      !livePerformance || !Number.isFinite(livePerformance.total_actions) || livePerformance.total_actions === 0;

    return {
      sentimentTrend: shouldFallbackSentiment ? DEMO_ANALYTICS.sentimentTrend : liveSentimentTrend,
      categories: shouldFallbackCategories ? DEMO_ANALYTICS.categories : liveCategories,
      heatmap: shouldFallbackHeatmap ? DEMO_ANALYTICS.heatmap : liveHeatmap,
      atRisk: liveAtRisk.length ? liveAtRisk : DEMO_ANALYTICS.atRisk,
      performance: shouldFallbackPerformance ? DEMO_ANALYTICS.performance : livePerformance,
    };
  },

  async searchKnowledgeBase(q: string): Promise<RagSource[]> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return [];
    const res = await safeRequest<{ results: RagSource[] }>(
      `/rag/search?q=${encodeURIComponent(q)}`,
      undefined,
      { results: [] }
    );
    return res?.results || [];
  },

  async dryRunAgent(emailId: number): Promise<AgentRunResponse | null> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return null;
    // Note: corrected from GET in legacy code to POST in backend router
    return safeRequest<AgentRunResponse>(`/agent/dry-run/${emailId}`, { method: 'POST' }, null);
  },

  async generateDraft(emailId: number): Promise<DraftGenerationResponse | null> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return null;
    return safeRequest<DraftGenerationResponse>(`/agent/draft/${emailId}`, { method: 'POST' }, null);
  },

  async getReputation(company: string): Promise<any> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) return null;
    return safeRequest<any>(`/intelligence/reputation?company=${encodeURIComponent(company)}`, undefined, null);
  },

  async simulateStream(request: SimulationRequest): Promise<SimulationResponse | null> {
    const isLive = useStore.getState().connectionState === 'live';
    if (!isLive) {
      // Return a simulated response after a small delay
      await new Promise((r) => setTimeout(r, 1500));
      return {
        source_path: request.source_path,
        total_loaded: 10,
        processed: request.limit || 5,
        succeeded: request.limit || 5,
        failed: 0,
        deduplicated: 0,
        elapsed_seconds: 1.24,
        replay_rate_per_second: request.emails_per_second,
        results: Array.from({ length: request.limit || 5 }, (_, i) => ({
          index: i,
          message_id: `sim_msg_${i}`,
          thread_id: `sim_thread_${i}`,
          sender: `sim_sender_${i}@test-company.com`,
          timestamp: new Date().toISOString(),
          status: 'Ingested',
          deduplicated: false,
          job_id: `job_${i}`,
          email_id: i + 100,
          error: null,
        })),
      };
    }

    return safeRequest<SimulationResponse | null>(
      '/api/simulate/stream',
      {
        method: 'POST',
        body: JSON.stringify(request),
      },
      null
    );
  },
};

function normalizeSentiment(score: number): string {
  if (score <= -0.4) return 'Negative';
  if (score >= 0.4) return 'Positive';
  return 'Neutral';
}

function inferCompany(sender: string = ''): string {
  return sender.includes('@')
    ? sender.split('@')[1].replace(/\..*$/, '').replace(/-/g, ' ')
    : sender;
}

function normalizeThreadRow(thread: any, contact: any): Thread {
  const emails = [...(thread.emails || [])].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  const latest = emails[emails.length - 1] || {};
  const latestScore = latest.sentiment_score ?? 0;
  const latestReasoning = latest.actions?.[0]?.agent_reasoning_log || [];
  const latestRag = latest.rag_context?.results || [];
  const latestMarket = latest.actions?.[0]?.tool_output?.market_intelligence_block || null;
  const contactProfile = contact || {};

  const id = String(thread.thread_id || thread.id);
  const fallbackMatch = DEMO_THREADS.find((t) => t.id === id);

  return {
    id,
    sender: thread.sender_email || contactProfile.email || '',
    company: contactProfile.company || inferCompany(thread.sender_email || contactProfile.email || ''),
    subject: thread.subject || latest.subject || '(no subject)',
    category: latest.category || thread.category || (normalizeSentiment(latestScore) === 'Negative' ? 'Complaint' : 'Inquiry'),
    urgency: latest.urgency || (thread.status === 'Escalated' ? 'High' : 'Low'),
    sentiment: latest.sentiment || normalizeSentiment(latestScore),
    sentimentScore: typeof latestScore === 'number' ? latestScore : 0,
    status: thread.status || 'Open',
    requiresHuman: Boolean(latest.requires_human ?? thread.status !== 'Open'),
    lastActivity: thread.last_updated_at || latest.timestamp || thread.first_seen_at,
    priority: thread.priority_score ?? latest.priority_score ?? 0,
    messages: emails.map((email) => ({
      id: email.id || email.message_id,
      emailId: typeof email.id === 'number' ? email.id : null,
      subject: email.subject || '(no subject)',
      body: email.body || '',
      sentimentScore: email.sentiment_score ?? 0,
      timestamp: email.timestamp,
    })),
    contact: {
      status: contactProfile.status || 'Active',
      accountValue: Number(contactProfile.account_value || 0),
      churnRiskScore: Number(contactProfile.churn_risk_score || 0),
      vipReason: contactProfile.vip_reason || null,
      openThreads: contactProfile.open_threads || 0,
      openTicketCount: contactProfile.open_ticket_count || 0,
      subscriptionTier: contactProfile.subscription_tier || null,
      renewalStatus: contactProfile.renewal_status || null,
    },
    reasoning: latestReasoning.length
      ? latestReasoning
      : fallbackMatch?.reasoning || [],
    rag: latestRag.length
      ? latestRag
      : fallbackMatch?.rag || [],
    market: latestMarket || fallbackMatch?.market || null,
    entities: latest.raw_entities || fallbackMatch?.entities || {},
    executiveSummary:
      thread.executive_summary ||
      fallbackMatch?.executiveSummary ||
      null,
  };
}

function mergeThreadRows(existingRows: Thread[], incomingRows: Thread[]): Thread[] {
  const merged = new Map<string, Thread>(existingRows.map((row) => [row.id, row]));
  incomingRows.forEach((row) => {
    merged.set(row.id, row);
  });
  return [...merged.values()];
}
