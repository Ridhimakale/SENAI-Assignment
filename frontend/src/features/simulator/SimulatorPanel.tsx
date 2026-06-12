import * as React from 'react';
import { useSimulateStream } from '../../services/queries';
import { SimulationRequest, SimulationResultItem } from '../../types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import {
  Play,
  Terminal,
  Activity,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  Database,
  Timer,
  Info,
} from 'lucide-react';
import { useStore } from '../../store';

export function SimulatorPanel() {
  const { connectionState } = useStore();
  const simulateMutation = useSimulateStream();

  // Form states
  const [sourcePath, setSourcePath] = React.useState('email-data-advanced.json');
  const [emailsPerSec, setEmailsPerSec] = React.useState(1.0);
  const [startIndex, setStartIndex] = React.useState(0);
  const [limit, setLimit] = React.useState<number | ''>('');
  const [failFast, setFailFast] = React.useState(false);
  const [dryRun, setDryRun] = React.useState(false);

  // Simulation output log
  const [results, setResults] = React.useState<SimulationResultItem[]>([]);
  const [stats, setStats] = React.useState<any>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setResults([]);
    setStats(null);

    const payload: SimulationRequest = {
      source_path: sourcePath,
      emails_per_second: Number(emailsPerSec),
      start_index: Number(startIndex),
      limit: limit === '' ? null : Number(limit),
      fail_fast: failFast,
      dry_run: dryRun,
    };

    simulateMutation.mutate(payload, {
      onSuccess: (data) => {
        if (data) {
          setResults(data.results);
          setStats({
            processed: data.processed,
            succeeded: data.succeeded,
            failed: data.failed,
            deduplicated: data.deduplicated,
            elapsed: data.elapsed_seconds,
            rate: data.replay_rate_per_second,
          });
        }
      },
    });
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-200 pb-5 select-none">
        <div className="space-y-0.5">
          <h2 className="text-lg font-bold text-neutral-900 tracking-tight">Event Replay Control Room</h2>
          <p className="text-sm text-neutral-500 font-medium">
            Simulate dynamic CRM email streams to evaluate AI ingestion pipelines and auto-classification heuristics.
          </p>
        </div>
        
        {connectionState === 'demo' && (
          <Badge variant="warning" className="h-6 gap-1 px-2.5 self-start md:self-center font-bold text-xs">
            <Info size={12} />
            <span>Mock Simulation Sandbox</span>
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT COLUMN: Simulation settings */}
        <Card className="border-neutral-200 bg-white h-fit shadow-sm select-none">
          <CardHeader className="p-5 border-b border-neutral-100">
            <CardTitle className="text-sm font-bold text-neutral-800 uppercase tracking-wider flex items-center gap-1.5">
              <Database size={14} className="text-neutral-400" />
              <span>Simulation Settings</span>
            </CardTitle>
            <CardDescription className="text-xs text-neutral-400 font-medium">
              Configure parameters to stream raw emails from dataset.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5">
            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div className="space-y-1">
                <label className="text-xs font-bold text-neutral-400 uppercase">Dataset JSON Path</label>
                <Input
                  type="text"
                  value={sourcePath}
                  onChange={(e) => setSourcePath(e.target.value)}
                  className="h-9.5 font-mono text-sm border-neutral-200"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-neutral-400 uppercase">Emails / Second</label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={emailsPerSec}
                    onChange={(e) => setEmailsPerSec(Number(e.target.value))}
                    className="h-9.5 text-sm border-neutral-200"
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-neutral-400 uppercase">Start Index</label>
                  <Input
                    type="number"
                    min="0"
                    value={startIndex}
                    onChange={(e) => setStartIndex(Number(e.target.value))}
                    className="h-9.5 text-sm border-neutral-200"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-neutral-400 uppercase">Max Email Count (Limit)</label>
                <Input
                  type="number"
                  placeholder="Replay entire dataset"
                  value={limit}
                  onChange={(e) => setLimit(e.target.value === '' ? '' : Number(e.target.value))}
                  className="h-9.5 text-sm border-neutral-200"
                />
              </div>

              {/* Toggles */}
              <div className="space-y-3 pt-2">
                <label className="flex items-center gap-2.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={failFast}
                    onChange={(e) => setFailFast(e.target.checked)}
                    className="rounded border-neutral-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4 cursor-pointer"
                  />
                  <div>
                    <span className="text-xs font-semibold text-neutral-700">Fail Fast</span>
                    <p className="text-[10px] text-neutral-400 font-medium leading-tight mt-0.5">Stop stream immediately if an email fails ingestion.</p>
                  </div>
                </label>

                <label className="flex items-center gap-2.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={dryRun}
                    onChange={(e) => setDryRun(e.target.checked)}
                    className="rounded border-neutral-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4 cursor-pointer"
                  />
                  <div>
                    <span className="text-xs font-semibold text-neutral-700">Dry Run</span>
                    <p className="text-[10px] text-neutral-400 font-medium leading-tight mt-0.5">Normalize and classify emails without writing database threads.</p>
                  </div>
                </label>
              </div>

              <Button
                type="submit"
                variant="default"
                className="w-full bg-neutral-900 text-white hover:bg-neutral-800 h-9.5 text-sm font-semibold gap-1.5 pt-1"
                disabled={simulateMutation.isPending}
              >
                {simulateMutation.isPending ? (
                  <>
                    <Activity size={12} className="animate-pulse" />
                    <span>Ingesting Stream...</span>
                  </>
                ) : (
                  <>
                    <Play size={12} />
                    <span>Run Simulation</span>
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* RIGHT COLUMN: Terminal Logs & Results (Spans 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Terminal Console log */}
          <Card className="border-neutral-200 bg-white overflow-hidden shadow-sm flex flex-col h-full">
            <CardHeader className="p-5 border-b border-neutral-100 flex flex-row items-center justify-between select-none">
              <div>
                <CardTitle className="text-sm font-bold text-neutral-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Terminal size={14} className="text-neutral-400" />
                  <span>Real-time Log Console</span>
                </CardTitle>
                <CardDescription className="text-xs text-neutral-400 font-medium">
                  Dynamic terminal capture of active ingest transactions.
                </CardDescription>
              </div>
              
              {stats && (
                <div className="text-xs text-neutral-400 font-medium">
                  Elapsed: <strong className="text-neutral-700 font-bold">{stats.elapsed}s</strong>
                </div>
              )}
            </CardHeader>
            <CardContent className="p-5 flex-1 flex flex-col min-h-[400px]">
              {/* Stats Strip */}
              {stats && (
                <div className="grid grid-cols-4 gap-3 mb-4 select-none">
                  {[
                    { label: 'Processed', value: stats.processed },
                    { label: 'Succeeded', value: stats.succeeded, color: 'text-emerald-600' },
                    { label: 'Failed', value: stats.failed, color: stats.failed > 0 ? 'text-red-600' : 'text-neutral-500' },
                    { label: 'Deduplicated', value: stats.deduplicated, color: 'text-indigo-600' },
                  ].map((s) => (
                    <div key={s.label} className="bg-neutral-50 border border-neutral-100 rounded-md p-2 text-center">
                      <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wide block">
                        {s.label}
                      </span>
                      <strong className={`text-lg font-bold font-mono tracking-tight ${s.color || 'text-neutral-900'}`}>
                        {s.value}
                      </strong>
                    </div>
                  ))}
                </div>
              )}

              {/* Terminal Box */}
              <div className="flex-1 bg-neutral-900 border border-neutral-950 text-neutral-200 font-mono text-xs p-4 rounded-md overflow-y-auto space-y-1.5 h-64 leading-normal select-text">
                {simulateMutation.isPending && (
                  <div className="text-indigo-400 animate-pulse">
                    &gt; Initializing stream reader from {sourcePath}...
                  </div>
                )}
                
                {results.length === 0 && !simulateMutation.isPending && (
                  <div className="text-neutral-500">
                    &gt; Console idle. Click "Run Simulation" to execute a dataset ingestion pipeline.
                  </div>
                )}

                {results.map((res) => {
                  const isSuccess = res.status === 'Ingested' || res.status === 'Processed';
                  return (
                    <div key={res.index} className="flex flex-col border-b border-neutral-800/40 pb-1.5 text-xs">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-neutral-500 font-bold">[{res.index}]</span>
                        <span className="text-neutral-300 font-semibold text-xs">{res.sender}</span>
                        <span>-</span>
                        <span className="text-neutral-400 truncate max-w-[200px] text-xs" title={res.message_id}>
                          {res.message_id}
                        </span>
                        
                        <span className={`ml-auto font-bold uppercase text-[10px] ${
                          isSuccess ? 'text-emerald-400' : 'text-rose-400'
                        }`}>
                          {res.status}
                        </span>
                      </div>
                      
                      {res.job_id && (
                        <div className="text-[10px] text-neutral-500 mt-0.5">
                          Job ID: {res.job_id} | Email ID: {res.email_id || 'N/A'}
                          {res.deduplicated && <span className="text-indigo-400 font-bold ml-2">(Deduplicated Event)</span>}
                        </div>
                      )}

                      {res.error && (
                        <div className="text-rose-400 font-semibold mt-0.5 text-[10px]">
                          Error: {res.error}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

        </div>
      </div>
    </div>
  );
}
