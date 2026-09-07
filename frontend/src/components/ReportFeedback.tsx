import { useMutation } from '@tanstack/react-query';
import { apiPost } from '@/lib/api';
import type { FeedbackResponse } from '@/lib/types';
import { Button } from '@/components/ui/button';

export default function ReportFeedback({ simulationId }: { simulationId: string }) {
  const feedback = useMutation({ mutationFn: (rating: number) => apiPost<FeedbackResponse>('/feedback', { simulation_id: simulationId, rating }) });
  return <section className='mt-6 rounded-xl border bg-card p-5 print:hidden' data-testid='report-feedback'>
    <h2 className='font-heading font-bold' data-testid='feedback-heading'>Did this coaching help you know what to practise?</h2>
    <p className='mt-1 text-sm text-muted-foreground' data-testid='feedback-privacy'>Optional rating. No transcript text is included in usage analytics.</p>
    {feedback.isSuccess ? <p className='mt-3 text-sm text-emerald-700' data-testid='feedback-thanks'>Thank you — your feedback is saved.</p> : <div className='mt-3 flex flex-wrap gap-2'>{[1, 2, 3, 4, 5].map(n => <Button variant='outline' key={n} data-testid={`feedback-rating-${n}`} aria-label={`${n} out of 5 — ${n === 1 ? 'not helpful' : n === 5 ? 'very helpful' : 'helpfulness'}`} disabled={feedback.isPending} onClick={() => feedback.mutate(n)}>{n}{n === 1 ? ' · Not helpful' : n === 5 ? ' · Very helpful' : ''}</Button>)}</div>}
    {feedback.isError ? <p role='alert' className='mt-2 text-sm text-red-700' data-testid='feedback-error'>Could not save that rating. Choose it again to retry.</p> : null}
  </section>;
}