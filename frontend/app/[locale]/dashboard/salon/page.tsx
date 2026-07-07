'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useTranslations, useLocale } from 'next-intl';

interface Salon { id: number; name: string; address_city: string; is_verified: boolean; }

export default function SalonDashboard() {
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations('dashboard');
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const [salons, setSalons] = useState<Salon[]>([]);
  const [loading, setLoading] = useState(true);
  const [claimId, setClaimId] = useState('');
  const [claimCode, setClaimCode] = useState('');
  const [claimStep, setClaimStep] = useState<'form'|'verify'|'done'>('form');

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (!d) router.push(`${prefix}/login`); });
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
    else alert(t('error_salon_id'));
  };

  const verifyClaim = async () => {
    const r = await fetch(`/api/owner/claim/verify?salon_id=${claimId}&token=${claimCode}`, {
      method: 'POST', credentials: 'include',
    });
    if (r.ok) { setClaimStep('done'); fetch('/api/owner/salons', { credentials: 'include' }).then(r => r.json()).then(setSalons); }
    else alert(t('error_code'));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link href={prefix || '/'} className="text-xl font-bold text-pink-600">Lookla</Link>
          <span className="text-sm text-gray-600">{t('owner_panel')}</span>
        </div>
      </header>
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-xl font-bold text-gray-800 mb-6">{t('my_salons')}</h1>

        {loading ? <p className="text-gray-400 text-sm">{t('loading')}</p> :
          salons.length > 0 ? (
            <div className="space-y-3 mb-8">
              {salons.map(s => (
                <div key={s.id} className="bg-white rounded-xl p-4 flex items-center justify-between border border-gray-100">
                  <div>
                    <p className="font-medium text-gray-800">{s.name}</p>
                    <p className="text-sm text-gray-500">{s.address_city}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {s.is_verified && <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{t('verified')}</span>}
                    <Link href={`${prefix}/dashboard/salon/${s.id}`} className="text-xs bg-pink-50 text-pink-600 px-3 py-1.5 rounded-lg hover:bg-pink-100">{t('manage')}</Link>
                  </div>
                </div>
              ))}
            </div>
          ) : null
        }

        <div className="bg-white rounded-xl p-6 border border-gray-100">
          <h2 className="font-semibold text-gray-800 mb-4">
            {claimStep === 'done' ? t('claim_done') : t('add_salon')}
          </h2>
          {claimStep === 'form' && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500">{t('claim_desc')}</p>
              <div className="flex gap-2">
                <input type="number" value={claimId} onChange={e => setClaimId(e.target.value)}
                  placeholder="Salon ID" className="flex-1 px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
                <button onClick={requestClaim} disabled={!claimId}
                  className="px-4 py-2 bg-pink-600 text-white rounded-xl text-sm font-medium disabled:opacity-50">
                  {t('claim_request')}
                </button>
              </div>
            </div>
          )}
          {claimStep === 'verify' && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500">{t('verify_desc')}</p>
              <div className="flex gap-2">
                <input type="text" value={claimCode} onChange={e => setClaimCode(e.target.value.toUpperCase())}
                  placeholder={t('code_placeholder')} maxLength={6}
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-xl text-sm font-mono tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-pink-200" />
                <button onClick={verifyClaim} disabled={claimCode.length < 6}
                  className="px-4 py-2 bg-pink-600 text-white rounded-xl text-sm font-medium disabled:opacity-50">
                  {t('verify_btn')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
