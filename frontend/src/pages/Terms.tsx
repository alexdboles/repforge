import DataLayout from '@/components/DataLayout';
import { Link } from 'react-router-dom';

const sections = [
  ['purpose', 'A practice environment, not a performance guarantee', 'RepForge simulates fictional sales conversations and generates AI coaching. Scores are training estimates based on available transcript evidence, not objective employment assessments, certifications or promises of improved sales. AI can misunderstand speech and produce incorrect or biased feedback. Review it critically.'],
  ['use', 'Use it responsibly', 'Use information you are authorised to provide, preferably fictional product and prospect details. Do not upload confidential customer data, impersonate others, harass people, bypass access restrictions or abuse provider allowances. Keep your sign-in details private. This build is intended for adults practising professional sales skills.'],
  ['availability', 'What is available today', 'Voice depends on microphone permission, browser speech support and configured AI/ElevenLabs services. Typed practice is available as an alternative. Requests are rate-limited and shared usage allowances apply; practice is not unlimited. Google sign-in is integrated but its live provider handoff has a known upstream issue. Email/password and guest access remain available.'],
  ['cost', 'No billing claims', 'There is no implemented paid plan, subscription, checkout or billing portal in this build. No payment details are collected by RepForge. This is not a promise of permanent free availability; any future paid offering needs separate, clear terms and a real purchase flow.'],
  ['data', 'Your data and deletion', 'You retain your rights in information you provide. RepForge processes it to deliver practice, feedback and progress. You can export and permanently delete your own stored records. Erasure cannot recall a file already downloaded or automatically erase provider-held records and private backups. Deleting an account does not delete other people’s workspace records.'],
  ['safety', 'Not a crisis service', 'RepForge is not a therapist and is not monitored for emergencies. If you are in immediate danger, contact local emergency services or a crisis service and someone you trust nearby. You can leave a simulation at any time. AI safety responses are not a substitute for human support.'],
  ['status', 'Notice status', 'These are current product-use disclosures, not a claim of legal review. Legal operator identity, jurisdiction-specific terms and a verified contact route must be supplied by the app operator before a broader production launch. Changes to this notice do not retroactively erase your data or grant new workspace access.'],
];
export default function Terms() {
  return <DataLayout title='Clear expectations for practice.' eyebrow='Terms of use'>
    <div className='max-w-3xl space-y-8'>{sections.map(([id, title, text]) => <section key={id} data-testid={`terms-section-${id}`} className='border-b border-border pb-7'><h2 data-testid={`terms-title-${id}`} className='font-heading text-lg font-bold'>{title}</h2><p data-testid={`terms-copy-${id}`} className='mt-3 text-sm leading-7 text-muted-foreground'>{text}</p></section>)}
      <Link to='/privacy' data-testid='terms-privacy-link' className='inline-block text-sm font-semibold text-primary'>Read the privacy notice →</Link>
    </div>
  </DataLayout>;
}