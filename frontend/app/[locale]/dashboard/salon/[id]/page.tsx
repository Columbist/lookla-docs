'use client';
import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useLocale } from 'next-intl';

const DAYS = ['Δευτέρα','Τρίτη','Τετάρτη','Πέμπτη','Παρασκευή','Σάββατο','Κυριακή'];
const PLATFORMS = ['instagram','facebook','tiktok','youtube','website'];

type Tab = 'info' | 'services' | 'hours' | 'social';

interface Service { id?: number; name: string; name_el?: string; duration_min?: number; price_from?: string; price_to?: string; currency: string; }
interface Hour { day_of_week: number; open_time?: string; close_time?: string; is_closed: boolean; }
interface SocialLink { platform: string; url: string; }

export default function SalonManagePage() {
  const { id } = useParams() as { id: string };
  const locale = useLocale();
  const router = useRouter();
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const salonId = parseInt(id);

  const [tab, setTab] = useState<Tab>('info');
  const [salon, setSalon] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState('');

  // Info form
  const [info, setInfo] = useState({ name:'', description_el:'', phone_primary:'', phone_secondary:'', email:'', website:'', address_street:'', address_number:'' });

  // Services
  const [services, setServices] = useState<Service[]>([]);
  const [newSvc, setNewSvc] = useState<Service>({ name:'', currency:'EUR' });
  const [editingSvc, setEditingSvc] = useState<number|null>(null);

  // Hours
  const [hours, setHours] = useState<Hour[]>(
    Array.from({length:7}, (_,i) => ({ day_of_week: i+1, open_time:'09:00', close_time:'20:00', is_closed: i >= 6 }))
  );

  // Social
  const [social, setSocial] = useState<SocialLink[]>(PLATFORMS.map(p => ({ platform: p, url: '' })));

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (!d) router.push(`${prefix}/login`); });

    fetch(`/api/owner/salons/${salonId}`, { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) { router.push(`${prefix}/dashboard/salon`); return; }
        setSalon(d);
        setInfo({ name: d.name||'', description_el: d.description_el||'', phone_primary: d.phone_primary||'', phone_secondary: d.phone_secondary||'', email: d.email||'', website: d.website||'', address_street: d.address_street||'', address_number: d.address_number||'' });
        setServices(d.services || []);
        if (d.hours?.length) {
          setHours(Array.from({length:7}, (_,i) => {
            const h = d.hours.find((x: Hour) => x.day_of_week === i+1);
            return h || { day_of_week: i+1, open_time:'09:00', close_time:'20:00', is_closed: false };
          }));
        }
        const sl = PLATFORMS.map(p => { const found = d.social_links?.find((x: SocialLink) => x.platform === p); return { platform: p, url: found?.url || '' }; });
        setSocial(sl);
      });
  }, [salonId]);

  const flash = (msg: string) => { setSaved(msg); setTimeout(() => setSaved(''), 3000); };

  const saveInfo = async () => {
    setSaving(true);
    const r = await fetch(`/api/owner/salons/${salonId}`, { method:'PUT', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify(info) });
    setSaving(false);
    if (r.ok) flash('Αποθηκεύτηκε!'); else flash('Σφάλμα αποθήκευσης');
  };

  const saveHours = async () => {
    setSaving(true);
    const r = await fetch(`/api/owner/salons/${salonId}/hours`, { method:'PUT', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ hours }) });
    setSaving(false);
    if (r.ok) flash('Αποθηκεύτηκε!'); else flash('Σφάλμα αποθήκευσης');
  };

  const saveSocial = async () => {
    setSaving(true);
    const links = social.filter(s => s.url);
    const r = await fetch(`/api/owner/salons/${salonId}/social-links`, { method:'PUT', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify(links) });
    setSaving(false);
    if (r.ok) flash('Αποθηκεύτηκε!'); else flash('Σφάλμα αποθήκευσης');
  };

  const addService = async () => {
    if (!newSvc.name) return;
    const r = await fetch(`/api/owner/salons/${salonId}/services`, { method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify(newSvc) });
    if (r.ok) {
      const d = await r.json();
      setServices(s => [...s, { ...newSvc, id: d.id }]);
      setNewSvc({ name:'', currency:'EUR' });
      flash('Υπηρεσία προστέθηκε!');
    }
  };

  const deleteService = async (svcId: number) => {
    const r = await fetch(`/api/owner/salons/${salonId}/services/${svcId}`, { method:'DELETE', credentials:'include' });
    if (r.ok) setServices(s => s.filter(x => x.id !== svcId));
  };

  const updateService = async (svcId: number, updates: Partial<Service>) => {
    const r = await fetch(`/api/owner/salons/${salonId}/services/${svcId}`, { method:'PUT', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify(updates) });
    if (r.ok) { setServices(s => s.map(x => x.id === svcId ? {...x, ...updates} : x)); setEditingSvc(null); flash('Αποθηκεύτηκε!'); }
  };

  if (!salon) return <div className="min-h-screen flex items-center justify-center"><p className="text-gray-400 text-sm">Φόρτωση...</p></div>;

  const tabs: { key: Tab; label: string }[] = [
    { key:'info', label:'Πληροφορίες' },
    { key:'services', label:'Υπηρεσίες' },
    { key:'hours', label:'Ώρες' },
    { key:'social', label:'Social' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <Link href={`${prefix}/dashboard/salon`} className="text-gray-400 hover:text-gray-600">←</Link>
          <h1 className="font-semibold text-gray-800 truncate">{salon.name}</h1>
          {salon.is_verified && <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">Verified</span>}
          {saved && <span className="ml-auto text-xs text-green-600 font-medium">{saved}</span>}
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-4 pt-4">
        <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-6">
          {tabs.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`flex-1 py-1.5 text-sm font-medium rounded-lg transition-colors ${tab === t.key ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* INFO TAB */}
        {tab === 'info' && (
          <div className="bg-white rounded-2xl p-6 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="text-xs text-gray-500 mb-1 block">Όνομα σαλονιού</label>
                <input value={info.name} onChange={e => setInfo(f => ({...f, name: e.target.value}))} className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              </div>
              <div className="col-span-2">
                <label className="text-xs text-gray-500 mb-1 block">Περιγραφή (ελληνικά)</label>
                <textarea value={info.description_el} onChange={e => setInfo(f => ({...f, description_el: e.target.value}))} rows={3} className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-pink-200" />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Τηλέφωνο</label>
                <input value={info.phone_primary} onChange={e => setInfo(f => ({...f, phone_primary: e.target.value}))} className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Τηλέφωνο 2</label>
                <input value={info.phone_secondary} onChange={e => setInfo(f => ({...f, phone_secondary: e.target.value}))} className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Email</label>
                <input type="email" value={info.email} onChange={e => setInfo(f => ({...f, email: e.target.value}))} className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Website</label>
                <input value={info.website} onChange={e => setInfo(f => ({...f, website: e.target.value}))} className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Οδός</label>
                <input value={info.address_street} onChange={e => setInfo(f => ({...f, address_street: e.target.value}))} className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Αριθμός</label>
                <input value={info.address_number} onChange={e => setInfo(f => ({...f, address_number: e.target.value}))} className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              </div>
            </div>
            <button onClick={saveInfo} disabled={saving} className="w-full py-2.5 bg-pink-600 text-white rounded-xl text-sm font-semibold hover:bg-pink-700 disabled:opacity-50">
              {saving ? 'Αποθήκευση...' : 'Αποθήκευση'}
            </button>
          </div>
        )}

        {/* SERVICES TAB */}
        {tab === 'services' && (
          <div className="space-y-3">
            {services.map(svc => (
              <div key={svc.id} className="bg-white rounded-xl p-4 border border-gray-100">
                {editingSvc === svc.id ? (
                  <div className="space-y-2">
                    <input value={svc.name} onChange={e => setServices(s => s.map(x => x.id === svc.id ? {...x, name: e.target.value} : x))} className="w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm" placeholder="Όνομα υπηρεσίας" />
                    <div className="flex gap-2">
                      <input type="number" value={svc.duration_min||''} onChange={e => setServices(s => s.map(x => x.id === svc.id ? {...x, duration_min: parseInt(e.target.value)||undefined} : x))} className="w-24 px-3 py-1.5 border border-gray-200 rounded-lg text-sm" placeholder="min" />
                      <input type="number" step="0.01" value={svc.price_from||''} onChange={e => setServices(s => s.map(x => x.id === svc.id ? {...x, price_from: e.target.value} : x))} className="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm" placeholder="Τιμή από €" />
                      <input type="number" step="0.01" value={svc.price_to||''} onChange={e => setServices(s => s.map(x => x.id === svc.id ? {...x, price_to: e.target.value} : x))} className="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm" placeholder="Τιμή έως €" />
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => updateService(svc.id!, svc)} className="px-3 py-1.5 bg-pink-600 text-white rounded-lg text-xs font-medium">Αποθήκευση</button>
                      <button onClick={() => setEditingSvc(null)} className="px-3 py-1.5 text-gray-500 rounded-lg text-xs">Άκυρο</button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{svc.name}</p>
                      <p className="text-xs text-gray-400">
                        {svc.duration_min ? `${svc.duration_min}min` : ''}
                        {svc.price_from ? ` • από ${svc.price_from}€` : ''}
                        {svc.price_to ? ` έως ${svc.price_to}€` : ''}
                      </p>
                    </div>
                    <div className="flex gap-1">
                      <button onClick={() => setEditingSvc(svc.id!)} className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1">✏️</button>
                      <button onClick={() => deleteService(svc.id!)} className="text-xs text-red-300 hover:text-red-500 px-2 py-1">✕</button>
                    </div>
                  </div>
                )}
              </div>
            ))}

            <div className="bg-white rounded-xl p-4 border border-dashed border-gray-200 space-y-2">
              <p className="text-xs font-medium text-gray-500 mb-2">Νέα υπηρεσία</p>
              <input value={newSvc.name} onChange={e => setNewSvc(f => ({...f, name: e.target.value}))} className="w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm" placeholder="Όνομα υπηρεσίας *" />
              <div className="flex gap-2">
                <input type="number" value={newSvc.duration_min||''} onChange={e => setNewSvc(f => ({...f, duration_min: parseInt(e.target.value)||undefined}))} className="w-24 px-3 py-1.5 border border-gray-200 rounded-lg text-sm" placeholder="min" />
                <input type="number" step="0.01" value={newSvc.price_from||''} onChange={e => setNewSvc(f => ({...f, price_from: e.target.value}))} className="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm" placeholder="Τιμή από €" />
                <input type="number" step="0.01" value={newSvc.price_to||''} onChange={e => setNewSvc(f => ({...f, price_to: e.target.value}))} className="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm" placeholder="Τιμή έως €" />
              </div>
              <button onClick={addService} disabled={!newSvc.name} className="w-full py-2 bg-pink-600 text-white rounded-xl text-sm font-medium disabled:opacity-50 hover:bg-pink-700">
                + Προσθήκη υπηρεσίας
              </button>
            </div>
          </div>
        )}

        {/* HOURS TAB */}
        {tab === 'hours' && (
          <div className="bg-white rounded-2xl p-6 space-y-3">
            {hours.map((h, i) => (
              <div key={h.day_of_week} className={`flex items-center gap-3 py-2 ${h.is_closed ? 'opacity-50' : ''}`}>
                <span className="text-sm font-medium text-gray-700 w-20">{DAYS[i]}</span>
                <input type="time" value={h.open_time||'09:00'} disabled={h.is_closed}
                  onChange={e => setHours(hs => hs.map((x,j) => j===i ? {...x, open_time: e.target.value} : x))}
                  className="px-2 py-1.5 border border-gray-200 rounded-lg text-sm disabled:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-pink-200" />
                <span className="text-gray-300 text-sm">—</span>
                <input type="time" value={h.close_time||'20:00'} disabled={h.is_closed}
                  onChange={e => setHours(hs => hs.map((x,j) => j===i ? {...x, close_time: e.target.value} : x))}
                  className="px-2 py-1.5 border border-gray-200 rounded-lg text-sm disabled:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-pink-200" />
                <label className="flex items-center gap-1.5 ml-auto text-xs text-gray-500 cursor-pointer">
                  <input type="checkbox" checked={h.is_closed}
                    onChange={e => setHours(hs => hs.map((x,j) => j===i ? {...x, is_closed: e.target.checked} : x))}
                    className="accent-pink-600" />
                  Κλειστά
                </label>
              </div>
            ))}
            <button onClick={saveHours} disabled={saving} className="w-full py-2.5 mt-2 bg-pink-600 text-white rounded-xl text-sm font-semibold hover:bg-pink-700 disabled:opacity-50">
              {saving ? 'Αποθήκευση...' : 'Αποθήκευση ωρών'}
            </button>
          </div>
        )}

        {/* SOCIAL TAB */}
        {tab === 'social' && (
          <div className="bg-white rounded-2xl p-6 space-y-3">
            {social.map((s, i) => (
              <div key={s.platform} className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-600 w-24 capitalize">{s.platform}</span>
                <input value={s.url} onChange={e => setSocial(sl => sl.map((x,j) => j===i ? {...x, url: e.target.value} : x))}
                  placeholder={s.platform === 'website' ? 'https://...' : `https://${s.platform}.com/...`}
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              </div>
            ))}
            <button onClick={saveSocial} disabled={saving} className="w-full py-2.5 mt-2 bg-pink-600 text-white rounded-xl text-sm font-semibold hover:bg-pink-700 disabled:opacity-50">
              {saving ? 'Αποθήκευση...' : 'Αποθήκευση'}
            </button>
          </div>
        )}

        <div className="h-8" />
      </div>
    </div>
  );
}
