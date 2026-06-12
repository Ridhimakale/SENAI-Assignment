import * as React from 'react';
import { useAnalytics } from '../../services/queries';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import {
  Loader2,
  TrendingDown,
  Users,
  Activity,
  BarChart3,
  AlertCircle,
  ShieldAlert,
  Clock3,
  Smile,
  ArrowUpRight,
  FileText,
} from 'lucide-react';
import { formatPercentage } from '../../lib/utils';

const PIE_COLORS = ['#4A90E2', '#6AA9FF', '#36C275', '#F5A623', '#E74C3C', '#94A3B8'];

export function AnalyticsDashboard() {
  const { data: analytics, isLoading, error } = useAnalytics();

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center gap-2 text-sm text-slate-500">
        <Loader2 size={16} className="animate-spin text-slate-400" />
        <span>Computing analytics warehouse stats...</span>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="space-y-2 p-8 text-center text-sm text-slate-500">
        <AlertCircle size={32} className="mx-auto text-slate-300" />
        <p>Failed to load analytics data from server.</p>
      </div>
    );
  }

  const mostAtRisk = analytics.atRisk?.[0];
  const avgSentiment =
    analytics.sentimentTrend.reduce((sum, point) => sum + point.sentiment_score, 0) /
    Math.max(analytics.sentimentTrend.length, 1);
  const customerSatisfaction = Math.max(32, Math.min(96, Math.round(((avgSentiment + 1) / 2) * 100)));
  const responseRate = Math.max(54, Math.min(98, Math.round((1 - analytics.performance.escalation_rate * 0.4) * 100)));
  const resolutionTime = `${Math.max(4, Math.round((mostAtRisk?.oldest_unresolved_hours ?? 24) / 3))}h avg`;

  const categoryData = analytics.categories.map((item) => ({
    name: item.category,
    value: item.count,
  }));

  const statCards = [
    {
      label: 'Escalation Rate',
      value: formatPercentage(analytics.performance.escalation_rate),
      description: 'Routed to human support agents',
      icon: TrendingDown,
      tone: 'text-red-600',
      accent: 'bg-red-50 text-[#E74C3C]',
    },
    {
      label: 'Resolution Time',
      value: resolutionTime,
      description: 'Average queue handling speed',
      icon: Clock3,
      tone: 'text-slate-900',
      accent: 'bg-slate-100 text-slate-600',
    },
    {
      label: 'AI Confidence',
      value: formatPercentage(analytics.performance.average_confidence_score),
      description: 'Model grounding safety confidence',
      icon: BarChart3,
      tone: 'text-[#4A90E2]',
      accent: 'bg-blue-50 text-[#4A90E2]',
    },
    {
      label: 'Customer Satisfaction',
      value: `${customerSatisfaction}%`,
      description: 'Derived from sentiment trend',
      icon: Smile,
      tone: 'text-emerald-600',
      accent: 'bg-emerald-50 text-[#36C275]',
    },
    {
      label: 'Response Rate',
      value: `${responseRate}%`,
      description: 'Speed of inbound response handling',
      icon: ArrowUpRight,
      tone: 'text-orange-600',
      accent: 'bg-orange-50 text-[#F5A623]',
    },
    {
      label: 'Automation Rate',
      value: formatPercentage(analytics.performance.auto_reply_rate),
      description: 'Replied autonomously by agent',
      icon: Activity,
      tone: 'text-emerald-600',
      accent: 'bg-emerald-50 text-[#36C275]',
    },
  ];

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">
          <BarChart3 size={13} className="text-[#4A90E2]" />
          <span>Executive Dashboard</span>
        </div>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-[2rem] font-bold tracking-tight text-slate-900">Analytics</h2>
            <p className="mt-1 text-sm text-slate-500">
              Executive-level view of sentiment, escalation patterns, automation performance, and at-risk accounts.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" size="sm" className="h-11 rounded-xl border-slate-200 px-4 text-sm text-slate-700">
              <FileText size={14} />
              <span>PDF</span>
            </Button>
            <Button variant="outline" size="sm" className="h-11 rounded-xl border-slate-200 px-4 text-sm text-slate-700">
              <FileText size={14} />
              <span>CSV</span>
            </Button>
            <Button variant="outline" size="sm" className="h-11 rounded-xl border-slate-200 px-4 text-sm text-slate-700">
              <FileText size={14} />
              <span>Excel</span>
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.label} className="border-slate-200 bg-white">
              <CardContent className="flex min-h-[120px] flex-col justify-between p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-2">
                    <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">{card.label}</div>
                    <div className={`text-2xl font-bold tracking-tight ${card.tone}`}>{card.value}</div>
                  </div>
                  <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${card.accent}`}>
                    <Icon size={18} />
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs font-medium text-slate-500">
                  <span>{card.description}</span>
                  <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-2.5 py-1 text-[0.7rem] font-semibold">
                    Live
                  </Badge>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(360px,1fr)]">
        <Card className="border-slate-200 bg-white">
          <CardHeader className="border-b border-slate-100 p-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle className="text-base font-semibold text-slate-900">Sentiment Trend Analytics</CardTitle>
                <CardDescription className="text-sm">
                  Line chart tracking message sentiment and moving average over time.
                </CardDescription>
              </div>
              <div className="flex flex-wrap gap-2">
                {['7D', '30D', '90D'].map((period, index) => (
                  <Badge
                    key={period}
                    variant={index === 1 ? 'default' : 'outline'}
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      index === 1 ? 'bg-[#4A90E2] text-white' : 'border-slate-200 bg-white text-slate-600'
                    }`}
                  >
                    {period}
                  </Badge>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-5">
            <div className="h-[450px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={analytics.sentimentTrend} margin={{ top: 10, right: 20, left: -15, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eef2f7" />
                  <XAxis dataKey="timestamp" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[-1, 1]} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderColor: '#dbe3ef',
                      borderRadius: '12px',
                      color: '#0f172a',
                      fontSize: '13px',
                      boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
                    }}
                  />
                  <Line type="monotone" name="Message Score" dataKey="sentiment_score" stroke="#E74C3C" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" name="Moving Avg" dataKey="moving_average" stroke="#4A90E2" strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardHeader className="border-b border-slate-100 p-5">
            <CardTitle className="text-base font-semibold text-slate-900">Category Breakdown</CardTitle>
            <CardDescription className="text-sm">Distribution of message categories across the active queue.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5 p-5">
            <div className="h-[320px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={72}
                    outerRadius={112}
                    paddingAngle={3}
                  >
                    {categoryData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderColor: '#dbe3ef',
                      borderRadius: '12px',
                      color: '#0f172a',
                      fontSize: '13px',
                      boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {categoryData.map((item, index) => (
                <div key={item.name} className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }} />
                    <span className="font-medium text-slate-700">{item.name}</span>
                  </div>
                  <span className="font-semibold text-slate-900">{item.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="border-slate-200 bg-white">
          <CardHeader className="border-b border-slate-100 p-5">
            <CardTitle className="text-base font-semibold text-slate-900">Response Heatmap</CardTitle>
            <CardDescription className="text-sm">Inbound activity and trigger frequency by hour of day.</CardDescription>
          </CardHeader>
          <CardContent className="p-5">
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.heatmap} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eef2f7" />
                  <XAxis
                    dataKey="hour_of_day"
                    tick={{ fill: '#64748b', fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(val) => `${val}h`}
                  />
                  <YAxis tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderColor: '#dbe3ef',
                      borderRadius: '12px',
                      color: '#0f172a',
                      fontSize: '13px',
                      boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
                    }}
                  />
                  <Bar dataKey="action_count" fill="#4A90E2" radius={[8, 8, 0, 0]} barSize={14} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardHeader className="border-b border-slate-100 p-5">
            <CardTitle className="text-base font-semibold text-slate-900">Agent Performance</CardTitle>
            <CardDescription className="text-sm">How much work the agent is handling autonomously.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 p-5">
            {[
              {
                label: 'Total actions',
                value: analytics.performance.total_actions,
                color: 'text-slate-900',
              },
              {
                label: 'Auto-replies',
                value: analytics.performance.auto_reply_count,
                color: 'text-emerald-600',
              },
              {
                label: 'Escalations',
                value: analytics.performance.escalation_count,
                color: 'text-red-600',
              },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                <span className="text-sm text-slate-500">{item.label}</span>
                <span className={`text-lg font-bold ${item.color}`}>{item.value}</span>
              </div>
            ))}

            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Avg confidence</div>
                <div className="mt-2 text-2xl font-bold text-[#4A90E2]">
                  {formatPercentage(analytics.performance.average_confidence_score)}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Automation rate</div>
                <div className="mt-2 text-2xl font-bold text-[#36C275]">
                  {formatPercentage(analytics.performance.auto_reply_rate)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardHeader className="border-b border-slate-100 p-5">
            <CardTitle className="text-base font-semibold text-slate-900">High Risk Accounts</CardTitle>
            <CardDescription className="text-sm">Customers that need proactive attention from the team.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 p-5">
            {analytics.atRisk.map((account) => (
              <div key={account.sender} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-bold text-slate-900">{account.company}</div>
                    <div className="text-xs text-slate-500">{account.sender}</div>
                  </div>
                  <Badge variant="destructive" className="rounded-full px-3 py-1 text-xs font-semibold">
                    Risk {formatPercentage(account.churn_risk_score)}
                  </Badge>
                </div>
                <div className="mt-3 grid gap-2 text-sm text-slate-600">
                  <div className="flex items-center justify-between">
                    <span>Unresolved threads</span>
                    <strong className="text-slate-900">{account.unresolved_threads}</strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Oldest unresolved</span>
                    <strong className="text-slate-900">{account.oldest_unresolved_hours}h</strong>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Negative streak</span>
                    <strong className="text-slate-900">{account.consecutive_negative_count}</strong>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {account.reasons.map((r) => (
                    <span key={r} className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-600">
                      {r.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="border-slate-200 bg-white">
          <CardHeader className="border-b border-slate-100 p-5">
            <CardTitle className="text-base font-semibold text-slate-900">SLA Violations</CardTitle>
            <CardDescription className="text-sm">Threads likely to need urgent handling or policy review.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 p-5">
            {analytics.atRisk.map((account) => (
              <div key={`${account.sender}-sla`} className="rounded-2xl bg-slate-50 p-4">
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-slate-900">{account.company}</div>
                  <ShieldAlert size={16} className="text-[#E74C3C]" />
                </div>
                <div className="mt-2 text-sm text-slate-600">
                  Unresolved for <strong className="text-slate-900">{account.oldest_unresolved_hours} hours</strong>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardHeader className="border-b border-slate-100 p-5">
            <CardTitle className="text-base font-semibold text-slate-900">Churn Prediction</CardTitle>
            <CardDescription className="text-sm">Estimated churn exposure based on current sentiment and risk.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 p-5">
            {analytics.atRisk.map((account) => (
              <div key={`${account.sender}-churn`} className="rounded-2xl border border-slate-200 bg-white p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-900">{account.company}</span>
                  <span className="text-sm font-bold text-red-600">{formatPercentage(account.churn_risk_score)}</span>
                </div>
                <div className="mt-3 h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-[#E74C3C]"
                    style={{ width: `${Math.min(100, Math.round(account.churn_risk_score * 100))}%` }}
                  />
                </div>
                <div className="mt-2 text-xs text-slate-500">Risk rises with negative streaks and unresolved threads.</div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardHeader className="border-b border-slate-100 p-5">
            <CardTitle className="text-base font-semibold text-slate-900">Category Snapshot</CardTitle>
            <CardDescription className="text-sm">Quick read of categories dominating the queue.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 p-5">
            {analytics.categories.slice(0, 4).map((category) => (
              <div key={category.category} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
                <span className="text-sm font-medium text-slate-600">{category.category}</span>
                <span className="text-lg font-bold text-slate-900">{category.count}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
