import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Search } from "lucide-react";
import { apiGet, apiPost } from "@/lib/api";
import { toast } from 'sonner';
import { formatDuration, getUserId, scoreTone } from "@/lib/profile";
import type { SimulationSummary } from "@/lib/types";
import AppShell from "@/components/AppShell";
import { DifficultyPips, EmptyState } from "@/components/Metrics";
import { Input } from "@/components/ui/input";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import DeleteDataDialog from '@/components/DeleteDataDialog';

export default function History() {
  const userId = getUserId();
  const [q, setQ] = useState("");
  const [offset, setOffset] = useState(0);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const qc = useQueryClient();
  const abandon = useMutation({ mutationFn: (id: string) => apiPost(`/simulations/${id}/abandon`), onSuccess: () => void qc.invalidateQueries({ queryKey: ['history', userId] }), onError: () => toast.error('Could not abandon this session. Please retry.') });
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["history", userId, offset],
    queryFn: () => apiGet<SimulationSummary[]>(`/users/${userId}/simulations?offset=${offset}&limit=50`),
    enabled: Boolean(userId),
    retry: false,
  });

  if (!userId) return <Navigate to="/" replace />;

  const rows = (data ?? []).filter((r) =>
    `${r.exercise_name} ${r.prospect_name} ${r.company} ${r.difficulty_name}`
      .toLowerCase()
      .includes(q.toLowerCase()),
  );

  return (
    <AppShell>
      <div data-testid="history-page">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-heading text-[30px] font-extrabold tracking-[-0.02em]">
              Session history
            </h1>
            <p className="mt-1.5 text-[14px] text-muted-foreground">
              Every call is stored with its full transcript and coaching debrief.
            </p>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              aria-label='Search this page of session history'
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search this page"
              className="w-[280px] pl-9"
              data-testid="history-search"
            />
          </div>
        </div>
        {isError ? <div role='alert' className='mt-5 text-sm' data-testid='history-error'>History could not load.<Button data-testid='history-retry' variant='outline' onClick={() => void refetch()}>Retry</Button></div> : null}

        {isLoading ? (
          <div className="mt-8 space-y-2" data-testid="history-loading">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded-md bg-secondary" />
            ))}
          </div>
        ) : null}

        {data && !data.length ? (
          <div className="mt-8">
            <EmptyState
              testid="history-empty"
              title="No sessions recorded yet"
              body="Once you complete a simulation it appears here with its transcript, tagged moments and full scorecard."
              action={
                <Link
                  to="/learn/cold-call?difficulty=2"
                  className={cn(buttonVariants(), "font-semibold")}
                  data-testid="history-empty-cta"
                >
                  Start Your First Simulation
                </Link>
              }
            />
          </div>
        ) : null}

        {rows.length ? (
          <div className="mt-7 overflow-hidden rounded-xl border border-border bg-card">
            <Table data-testid="history-table">
              <TableHeader>
                <TableRow>
                  <TableHead>Exercise</TableHead>
                  <TableHead>Prospect</TableHead>
                  <TableHead>Difficulty</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Turns</TableHead>
                  <TableHead className="text-right">Score</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((r) => (
                  <TableRow key={r.id} data-testid={`history-row-${r.id}`}>
                    <TableCell>
                      <div className="font-medium">{r.exercise_name}</div>
                      <div className="text-[12px] text-muted-foreground">
                        {new Date(r.started_at).toLocaleString()}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-[13.5px]">{r.prospect_name}</div>
                      <div className="text-[12px] text-muted-foreground">{r.company}</div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <DifficultyPips level={r.difficulty} />
                        <span className="text-[12.5px] text-muted-foreground">
                          {r.difficulty_name}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-[13px]">
                      {formatDuration(r.duration_seconds)}
                    </TableCell>
                    <TableCell className="font-mono text-[13px]">{r.turns}</TableCell>
                    <TableCell className="text-right">
                      {r.overall_score !== null ? (
                        <span
                          className={cn("font-mono text-[15px] font-bold", scoreTone(r.overall_score))}
                        >
                          {r.overall_score}
                        </span>
                      ) : (
                        <Badge variant="outline">{r.status.replace('_', ' ')}</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link
                        to={r.status === "completed" || r.status === 'abandoned' ? `/scorecard/${r.id}` : `/simulation/${r.id}`}
                        className="inline-flex items-center gap-1 text-[13px] font-medium text-primary"
                        data-testid={`history-open-${r.id}`}
                      >
                        {r.status === "completed" ? "Debrief" : "Resume"}
                        <ArrowRight className="size-3.5" />
                      </Link>
                      {['active', 'preparation'].includes(r.status) ? <Button size='xs' variant='ghost' className='ml-2' data-testid={`history-abandon-${r.id}`} disabled={abandon.isPending} onClick={() => abandon.mutate(r.id)}>Abandon</Button> : null}
                      <Button size='xs' variant='ghost' className='ml-2 text-red-700' data-testid={`history-delete-${r.id}`} onClick={() => setDeleteId(r.id)}>Delete</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : null}

        <div className='mt-5 flex items-center gap-3' data-testid='history-pagination'><Button variant='outline' data-testid='history-previous-page' disabled={offset === 0 || isLoading} onClick={() => setOffset(v => Math.max(0, v - 50))}>Previous</Button><span className='text-sm' data-testid='history-page-number'>Page {offset / 50 + 1} · 50 sessions per page</span><Button variant='outline' data-testid='history-next-page' disabled={!data || data.length < 50 || isLoading} onClick={() => setOffset(v => v + 50)}>Next</Button></div>

        {data && data.length && !rows.length ? (
          <p className="mt-6 text-[13.5px] text-muted-foreground" data-testid="history-no-match">
            No sessions match “{q}”.
          </p>
        ) : null}
        {deleteId && <DeleteDataDialog scope='session' sessionId={deleteId} onClose={() => setDeleteId(null)} />}
      </div>
    </AppShell>
  );
}
