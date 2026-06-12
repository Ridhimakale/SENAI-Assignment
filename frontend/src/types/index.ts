export interface Message {
  id: string | number;
  emailId?: number | null;
  subject: string;
  body: string;
  sentimentScore: number;
  timestamp: string;
}

export interface ContactProfile {
  status: string;
  accountValue: number;
  churnRiskScore: number;
  vipReason: string | null;
  openThreads?: number;
  openTicketCount?: number;
  subscriptionTier?: string | null;
  renewalStatus?: string | null;
}

export interface ReasoningTrace {
  thought: string;
  action: string;
  observation: string;
  next_step: string;
}

export interface AgentRunResponse {
  email_id: number;
  dry_run: boolean;
  reasoning_trace: ReasoningTrace[];
  proposed_actions: Array<{
    action_type: string;
    reason: string;
    would_execute: boolean;
    safety_block_reason?: string | null;
  }>;
  draft_preview: string | null;
  tool_call_count: number;
  max_tool_calls: number;
  final_status: string;
}

export interface DraftGenerationResponse {
  email_id: number;
  draft: string;
  policy_refs: string[];
  model_name?: string | null;
  provider?: string | null;
}

export interface RagSource {
  source_doc: string;
  score: number;
  chunk_text: string;
}

export interface Thread {
  id: string;
  sender: string;
  company: string;
  subject: string;
  category: string;
  urgency: string;
  sentiment: string;
  sentimentScore: number;
  status: string;
  requiresHuman: boolean;
  lastActivity: string;
  priority: number;
  messages: Message[];
  contact: ContactProfile;
  reasoning: ReasoningTrace[];
  rag: RagSource[];
  market: string | null;
  entities: Record<string, any>;
  executiveSummary?: string | null;
  assignedTo?: string;
}

export interface SentimentPoint {
  timestamp: string;
  sentiment_score: number;
  moving_average: number;
}

export interface CategoryPoint {
  category: string;
  count: number;
}

export interface HeatmapPoint {
  hour_of_day: number;
  action_count: number;
}

export interface AtRiskAccount {
  sender: string;
  company: string;
  churn_risk_score: number;
  unresolved_threads: number;
  oldest_unresolved_hours: number;
  consecutive_negative_count: number;
  reasons: string[];
}

export interface AgentPerformance {
  total_actions: number;
  auto_reply_count: number;
  escalation_count: number;
  auto_reply_rate: number;
  escalation_rate: number;
  average_confidence_score: number;
}

export interface AnalyticsData {
  sentimentTrend: SentimentPoint[];
  categories: CategoryPoint[];
  heatmap: HeatmapPoint[];
  atRisk: AtRiskAccount[];
  performance: AgentPerformance;
}

export interface DashboardStats {
  pending: number;
  replied: number;
  escalated: number;
  critical: number;
  spam: number;
  needs_human: number;
}

export interface SimulationRequest {
  source_path: string;
  emails_per_second: number;
  start_index: number;
  limit: number | null;
  fail_fast: boolean;
  dry_run: boolean;
}

export interface SimulationResultItem {
  index: number;
  message_id: string;
  thread_id: string;
  sender: string;
  timestamp: string;
  status: string;
  deduplicated: boolean;
  job_id: string | null;
  email_id: number | null;
  error: string | null;
}

export interface SimulationResponse {
  source_path: string;
  total_loaded: number;
  processed: number;
  succeeded: number;
  failed: number;
  deduplicated: number;
  elapsed_seconds: number;
  replay_rate_per_second: number;
  results: SimulationResultItem[];
}
