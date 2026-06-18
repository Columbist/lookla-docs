'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) { router.push('/login'); return; }
        setUser(d);
        if (d.role === 'salon_owner') router.push('/dashboard/salon');
        if (d.role === 'professional') router.push('/dashboard/master');
      });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <p className="text-4xl mb-4">💼</p>
        <h1 className="text-xl font-bold text-gray-800 mb-4">Πίνακας ελέγχου</h1>
        <div className="flex gap-3 justify-center">
          <Link href="/dashboard/salon" className="px-4 py-2 bg-pink-600 text-white rounded-xl text-sm">Ιδιοκτήτης σαλονιού</Link>
          <Link href="/dashboard/master" className="px-4 py-2 border border-pink-200 text-pink-600 rounded-xl text-sm">Ελεύθερος επαγγελματίας</Link>
        </div>
      </div>
    </div>
  );
}
