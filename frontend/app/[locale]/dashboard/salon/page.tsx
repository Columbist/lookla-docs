'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface Salon { id: number; name: string; address_city: string; is_verified: boolean; }

export default function SalonDashboard() {
  const router = useRouter();
  const [salons, setSalons] = useState<Salon[]>([]);
  const [loading, setLoading] = useState(true);
  const [claimId, setClaimId] = useState('');
  const [claimCode, setClaimCode] = useState('');
  const [claimStep, setClaimStep] = useState<'form'|'verify'|'done'>('form');

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (!d) router.push('/login'); });
    fetch('/api/owner/salons', { credentials: 'include' })
      .then(r => r.ok ? r.json() : [])
      .then(d => { setSalons(d); setLoading(false); });
  }, []);

  const requestClaim = async () => {
    const r = await fetch('/api/owner/claim/request', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ salon_id: parseInt(claimId), channel: 'email' }),
    });
    if (r.ok) setClaimStep('verify');
    else alert('Σφάλμα. Ελέγξτε το ID σαλονιού.');
  };

  const verifyClaim = async () => {
    const r = await fetch(`/api/owner/claim/verify?salon_id=${claimId}&token=${claimCode}`, {
      method: 'POST', credentials: 'include',
    });
    if (r.ok) { setClaimStep('done'); fetch('/api/owner/salons', { credentials: 'include' }).then(r => r.json()).then(setSalons); }
    else alert('Λάθος κωδικός.');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-pink-600">Lookla</Link>
          <span className="text-sm text-gray-600">Πίνακας ιδιοκτήτη</span>
        </div>
      </header>
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-xl font-bold text-gray-800 mb-6">Τα σαλόνια μου</h1>

        {/* Existing salons */}
        {loading ? <p className="text-gray-400 text-sm">Φόρτωση...</p> :
          salons.length > 0 ? (
            <div className="space-y-3 mb-8">
              {salons.map(s => (
                <div key={s.id} className="bg-white rounded-xl p-4 flex items-center justify-between border border-gray-100">
                  <div>
                    <p className="font-medium text-gray-800">{s.name}</p>
                    <p className="text-sm text-gray-500">{s.address_city}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {s.is_verified && <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">✓ Επαληθευμένο</span>}
                    <Link href={`/dashboard/salon/${s.id}`} className="text-xs bg-pink-50 text-pink-600 px-3 py-1.5 rounded-lg hover:bg-pink-100">Διαχείριση</Link>
                  </div>
                </div>
              ))}
            </div>
          ) : null
        }

        {/* Claim a salon */}
        <div className="bg-white rounded-xl p-6 border border-gray-100">
          <h2 className="font-semibold text-gray-800 mb-4">
            {claimStep === 'done' ? '✅ Το σαλόνι σας επαληθεύτηκε!' : 'Προσθήκη σαλονιού'}
          </h2>
          {claimStep === 'form' && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500">Βρείτε το σαλόνι σας στην αναζήτηση και αντιγράψτε το ID από το URL (/salons/ID)</p>
              <div className="flex gap-2">
                <input type="number" value={claimId} onChange={e => setClaimId(e.target.value)}
                  placeholder="Salon ID" className="flex-1 px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
                <button onClick={requestClaim} disabled={!claimId}
                  className="px-4 py-2 bg-pink-600 text-white rounded-xl text-sm font-medium disabled:opacity-50">
                  Αίτηση
                </button>
              </div>
            </div>
          )}
          {claimStep === 'verify' && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500">Εισάγετε τον κωδικό που στάλθηκε στο email/SMS του σαλονιού</p>
              <div className="flex gap-2">
                <input type="text" value={claimCode} onChange={e => setClaimCode(e.target.value.toUpperCase())}
                  placeholder="Κωδικός (6 ψηφία)" maxLength={6}
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-xl text-sm font-mono tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-pink-200" />
                <button onClick={verifyClaim} disabled={claimCode.length < 6}
                  className="px-4 py-2 bg-pink-600 text-white rounded-xl text-sm font-medium disabled:opacity-50">
                  Επαλήθευση
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
