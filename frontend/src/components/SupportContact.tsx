import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';
type SiteInfo = { operator: string; support_email: string; privacy_email: string };
export default function SupportContact() {
  const { data, isPending, isError } = useQuery({ queryKey: ['site-info'], queryFn: () => apiGet<SiteInfo>('/site-info') });
  if (isPending) return <p role='status'>Loading contact details…</p>;
  if (isError) return <p>Contact details could not be loaded. Please try again later.</p>;
  return <div className='space-y-3'>
    {data?.operator && <p>Operated by {data.operator}</p>}
    {data?.support_email && <p>Support: <a className='text-primary underline' href={`mailto:${data.support_email}`}>{data.support_email}</a></p>}
    {data?.privacy_email && <p>Privacy requests: <a className='text-primary underline' href={`mailto:${data.privacy_email}`}>{data.privacy_email}</a></p>}
    {!data?.support_email && !data?.privacy_email && <p>A verified contact address has not been configured yet.</p>}
    <p className='text-sm text-muted-foreground'>Do not email passwords, reset links, or confidential customer information.</p>
  </div>;
}
