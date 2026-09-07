import { Lightbulb } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function CoachObservation({ title, detail, quote, buyerQuote, onRetry, busy, sample = false }: {
  title: string; detail: string; quote?: string; buyerQuote?: string; onRetry?: () => void; busy?: boolean; sample?: boolean;
}) {
  const prefix = sample ? 'sample-coach' : 'report-coach';
  return <section className='mt-6 rounded-xl border border-slate-700 bg-[#0F172A] p-6 text-slate-100' data-testid={`${prefix}-observation`}>
    <p className='flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-300' data-testid={`${prefix}-label`}><Lightbulb className='size-4' />Coach’s highest-impact observation{sample ? ' · fictional example' : ''}</p>
    <h2 className='mt-3 font-heading text-xl font-bold' data-testid={`${prefix}-title`}>{title}</h2>
    <p className='mt-3 text-sm leading-relaxed text-slate-300' data-testid={`${prefix}-detail`}>{detail}</p>
    {buyerQuote ? <blockquote className='mt-3 rounded bg-slate-800 p-3 text-sm' data-testid={`${prefix}-buyer-exchange`}>Buyer: “{buyerQuote}”</blockquote> : null}
    {quote ? <blockquote className='mt-2 rounded bg-slate-800 p-3 text-sm' data-testid={`${prefix}-evidence`}>Evidence from the transcript: “{quote}”</blockquote> : null}
    {onRetry ? <Button className='mt-4' data-testid={`${prefix}-retry`} disabled={busy} onClick={onRetry}>Retry this exact moment</Button> : null}
  </section>;
}