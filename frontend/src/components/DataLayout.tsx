import { Link } from 'react-router-dom';
import { Headphones, ArrowLeft, ShieldCheck } from 'lucide-react';
import PrivacyLinks from './PrivacyLinks';

export default function DataLayout({ title, eyebrow, children }: { title: string; eyebrow: string; children: React.ReactNode }) {
  return <div className='min-h-screen bg-background' data-testid='data-layout'>
    <header className='border-b border-border bg-white/90'><div className='mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-5 px-6 py-5'>
      <Link to='/' data-testid='data-brand-link' className='flex items-center gap-2 font-heading text-lg font-extrabold'><span className='rounded-md bg-slate-900 p-2 text-white'><Headphones className='size-4' /></span>RepForge</Link>
      <PrivacyLinks prefix='data-nav' />
    </div></header>
    <main className='mx-auto max-w-5xl px-6 py-10 sm:py-14'>
      <Link to='/profile' data-testid='data-back-profile' className='inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-primary'><ArrowLeft className='size-4' />Back to profile</Link>
      <div className='mb-10 mt-8 max-w-2xl'><p data-testid='data-eyebrow' className='mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-primary'><ShieldCheck className='size-4' />{eyebrow}</p><h1 data-testid='data-heading' className='font-heading text-3xl font-extrabold tracking-tight sm:text-4xl'>{title}</h1></div>
      {children}
    </main>
    <footer className='mx-auto max-w-5xl border-t border-border px-6 py-7 text-xs text-muted-foreground' data-testid='data-footer'>RepForge · Practice the conversation before it counts.</footer>
  </div>;
}