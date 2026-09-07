import { Link } from 'react-router-dom';

export default function PrivacyLinks({ prefix }: { prefix: string }) {
  return <nav aria-label='Privacy and data' className='flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground'>
    {['Privacy', 'Terms', 'Data', 'Support'].map(label => <Link key={label} to={`/${label.toLowerCase()}`} data-testid={`${prefix}-${label.toLowerCase()}-link`} className='transition-colors hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-4'>{label === 'Data' ? 'Your data & controls' : label}</Link>)}
  </nav>;
}