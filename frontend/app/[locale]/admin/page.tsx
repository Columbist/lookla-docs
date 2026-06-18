'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface Stats { total_salons: number; verified_salons: number; needs_review: number; total_pros: number; total_users: number; bookings_today: number; total_bookings: number; open_reports: number; moderation_pending: number; }

export default function AdminPage({ params }: { params: { locale: string } }) {
  const locale = (params as any).locale ?? 'el';
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [salons, setSalons] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [tab, setTab] = useState<'overview'|'salons'|'reports'|'moderation'>('overview');

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (!d || d.role !== 'admin') router.push('/'); });
    fetch('/api/admin/stats', { credentials: 'include' }).then(r => r.json()).then(setStats).catch(() => {});
    fetch('/api/admin/salons?needs_review=true&limit=20', { credentials: 'include' }).then(r => r.json()).then(d => setSalons(d.items || [])).catch(() => {});
    fetch('/api/admin/reports?status=open', { credentials: 'include' }).then(r => r.json()).then(setReports).catch(() => {});
  }, []);

  const approveReport = async (id: number, status: string) => {
    await fetch(`/api/admin/reports/${id}`, { method: 'PATCH', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({status}) });
    setReports(r => r.filter(x => x.id !== id));
  };

  const salonAction = async (id: number, updates: Record<string, boolean>) => {
    await fetch(`/api/admin/salons/${id}`, { method: 'PATCH', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify(updates) });
    setSalons(s => s.map(x => x.id === id ? {...x, ...updates} : x));
  };

  const prefix = locale === 'el' ? '' : `/${locale}`;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link href={prefix || '/'} className="text-xl font-bold text-pink-600">Lookla <span className="text-xs text-gray-500 font-normal">Admin</span></Link>
          <nav className="flex gap-1">
            {(['overview','salons','reports','moderation'] as const).map(t => (
              <button key={t} onClick={() => setTab(t)} className={`px-3 py-1.5 rounded-lg text-sm ${tab === t ? 'bg-pink-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>{t}</button>
            ))}
          </nav>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {tab === 'overview' && stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Σαλόνια', value: stats.total_salons, sub: `${stats.verified_salons} verified` },
              { label: 'Επαγγελματίες', value: stats.total_pros, sub: '' },
              { label: 'Χρήστες', value: stats.total_users, sub: '' },
              { label: 'Κρατήσεις σήμερα', value: stats.bookings_today, sub: `${stats.total_bookings} σύνολο` },
              { label: 'Υπό έλεγχο', value: stats.needs_review, sub: 'σαλόνια', warn: stats.needs_review > 0 },
              { label: 'Αναφορές', value: stats.open_reports, sub: 'ανοιχτές', warn: stats.open_reports > 0 },
              { label: 'Αναμένει έλεγχο', value: stats.moderation_pending, sub: 'περιεχόμενο', warn: stats.moderation_pending > 0 },
              { label: 'Σύνολο κρατήσεων', value: stats.total_bookings, sub: 'όλων των εποχών' },
            ].map(s => (
              <div key={s.label} className={`bg-white rounded-xl p-4 border ${s.warn ? 'border-orange-200 bg-orange-50' : 'border-gray-100'}`}>
                <p className={`text-2xl font-bold ${s.warn ? 'text-orange-600' : 'text-gray-800'}`}>{s.value}</p>
                <p className="text-sm font-medium text-gray-700">{s.label}</p>
                {s.sub && <p className="text-xs text-gray-400">{s.sub}</p>}
              </div>
            ))}
          </div>
        )}

        {tab === 'salons' && (
          <div className="bg-white rounded-xl overflow-hidden border border-gray-100">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h2 className="font-semibold text-sm text-gray-700">Σαλόνια υπό έλεγχο ({salons.length})</h2>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs">
                <tr>
                  <th className="px-4 py-2 text-left">Όνομα</th>
                  <th className="px-4 py-2 text-left">Πόλη</th>
                  <th className="px-4 py-2 text-left">Κατάσταση</th>
                  <th className="px-4 py-2 text-left">Ενέργειες</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {salons.map(s => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800">{s.name}</td>
                    <td className="px-4 py-3 text-gray-500">{s.address_city}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {s.is_verified && <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">Verified</span>}
                        {s.needs_review && <span className="text-xs bg-orange-50 text-orange-600 px-1.5 py-0.5 rounded">Review</span>}
                        {!s.is_active && <span className="text-xs bg-red-50 text-red-600 px-1.5 py-0.5 rounded">Inactive</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        <button onClick={() => salonAction(s.id, {needs_review: false, is_verified: true})} className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded hover:bg-green-100">✓ Approve</button>
                        <button onClick={() => salonAction(s.id, {is_active: !s.is_active})} className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded hover:bg-red-100">{s.is_active ? 'Deactivate' : 'Activate'}</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === 'reports' && (
          <div className="bg-white rounded-xl overflow-hidden border border-gray-100">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h2 className="font-semibold text-sm text-gray-700">Αναφορές ({reports.length})</h2>
            </div>
            <div className="divide-y">
              {reports.map(r => (
                <div key={r.id} className="px-4 py-3 flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{r.salon_name || `Salon #${r.salon_id}`}</p>
                    <p className="text-xs text-orange-600 mt-0.5">{r.reason}</p>
                    {r.description && <p className="text-xs text-gray-500 mt-0.5">{r.description}</p>}
                    <p className="text-xs text-gray-400 mt-1">{new Date(r.created_at).toLocaleDateString('el-GR')}</p>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <button onClick={() => approveReport(r.id, 'resolved')} className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded">Λύθηκε</button>
                    <button onClick={() => approveReport(r.id, 'dismissed')} className="text-xs bg-gray-50 text-gray-600 px-2 py-1 rounded">Απόρριψη</button>
                  </div>
                </div>
              ))}
              {reports.length === 0 && <p className="p-4 text-sm text-gray-400">Δεν υπάρχουν αναφορές</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
