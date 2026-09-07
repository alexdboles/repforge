import { Link } from 'react-router-dom';
import SupportContact from '@/components/SupportContact';
export default function Support() {
  return <main className='mx-auto max-w-xl px-6 py-16'><Link to='/' className='font-bold'>RepForge</Link><h1 className='my-8 text-3xl font-bold'>Support & privacy contact</h1><SupportContact /><Link className='mt-8 block text-primary' to='/forgot-password'>Recover your account</Link></main>;
}
