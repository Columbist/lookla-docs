'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useTranslations, useLocale } from 'next-intl';

const SPECIALTIES = ['Nail technician','Makeup artist','Hair colorist','Lash & brow artist','Massage therapist','Hair stylist','Barber','Tattoo artist'];
const DAYS = ['Δευτέρα','Τρίτη','Τετάρτη','Πέμπτη','Παρασκευή','Σάββατο','Κυριακή'];
const PLATFORMS = ['instagram','facebook','tiktok','youtube','website'];

type Section = 'none' | 'availability' | 'social';

export default function MasterDashboard() {
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations('dashboard');
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const [profile, setProfile] = useState<any>(null);
  const [form, setForm] = useState({ name:'', specialty:'', bio_el:'', phone:'', base_city:'', service_radius_km:15, does_home_visits:true, has_home_studio:false });
  const [step, setStep] = useState<'loading'|'create'|'profile'>('loading');
  const [openSection, setOpenSection] = useState<Section>('none');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState('');

  const [avail, setAvail] = useState(
    Array.from({length:7}, (_,i) => ({ day_of_week: i+1, start_time:'09:00', end_time:'20:00', is_available: i < 5 }))
  );
  const [social, setSocial] = useState(PLATFORMS.map(p => ({ platform: p, url: '' })));

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' }).then(r => r.ok ? r.json() : null).then(d => { if (!d) router.push(`${prefix}/login`); });
    fetch('/api/masters/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d) {
          setProfile(d);
          setStep('profile');
          if (d.availability?.length) {
            setAvail(Array.from({length:7}, (_,i) => {
              const found = d.availability.find((x: any) => x.day_of_week === i+1);
              return found || { day_of_week: i+1, start_time:'09:00', end_time:'20:00', is_available: false };
            }));
          }
          if (d.social_links?.length) {
            setSocial(PLATFORMS.map(p => { const f = d.social_links.find((x: any) => x.platform === p); return { platform: p, url: f?.url || '' }; }));
          }
        } else {
          setStep('create');
        }
      });
  }, []);

  const flash = (msg: string) => { setSaved(msg); setTimeout(() => setSaved(''), 3000); };

  const createProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    const r = await fetch('/api/masters/register', { method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify(form) });
    if (r.ok) { const d = await r.json(); setProfile(d); setStep('profile'); }
    else alert(t('error_create'));
  };

  const saveAvailability = async () => {
    setSaving(true);
    const r = await fetch('/api/masters/me/availability', { method:'PUT', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ schedule: avail }) });
    setSaving(false);
    if (r.ok) { flash('Αποθηκεύτηκε!'); setOpenSection('none'); }
  };

  const saveSocial = async () => {
    setSaving(true);
    const links = social.filter(s => s.url);
    const r = await fetch('/api/masters/me/social-links', { method:'PUT', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ links }) });
    setSaving(false);
    if (r.ok) { flash('Αποθηκεύτηκε!'); setOpenSection('none'); }
  };

  const toggle = (s: Section) => setOpenSection(o => o === s ? 'none' : s);

  if (step === 'loading') return <div className="min-h-screen flex items-center justify-center"><p className="text-gray-400">{t('loading')}</p></div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <Link href={prefix || '/'} className="text-xl font-bold text-pink-600">Lookla</Link>
          <div className="flex items-center gap-3">
            {saved && <span className="text-xs text-green-600 font-medium">{saved}</span>}
            <span className="text-sm text-gray-600">{t('master_profile')}</span>
          </div>
        </div>
      </header>
      <div className="max-w-2xl mx-auto px-4 py-8">
        {step === 'create' ? (
          <div className="bg-white rounded-2xl p-6">
            <h1 className="text-xl font-bold text-gray-800 mb-2">{t('create_title')}</h1>
            <p className="text-sm text-gray-500 mb-6">{t('create_desc')}</p>
            <form onSubmit={createProfile} className="space-y-4">
              <input required placeholder={t('name_placeholder')} value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))} className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              <select required value={form.specialty} onChange={e => setForm(f => ({...f, specialty: e.target.value}))} className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-700">
                <option value="">{t('specialty_placeholder')}</option>
                {SPECIALTIES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <textarea placeholder={t('bio_placeholder')} value={form.bio_el} onChange={e => setForm(f => ({...f, bio_el: e.target.value}))} className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm h-24 resize-none focus:outline-none focus:ring-2 focus:ring-pink-200" />
              <input placeholder={t('phone_placeholder')} value={form.phone} onChange={e => setForm(f => ({...f, phone: e.target.value}))} className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              <input placeholder={t('city_placeholder')} value={form.base_city} onChange={e => setForm(f => ({...f, base_city: e.target.value}))} className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input type="checkbox" checked={form.does_home_visits} onChange={e => setForm(f => ({...f, does_home_visits: e.target.checked}))} className="accent-pink-600" />
                  {t('home_visits')}
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input type="checkbox" checked={form.has_home_studio} onChange={e => setForm(f => ({...f, has_home_studio: e.target.checked}))} className="accent-pink-600" />
                  {t('home_studio')}
                </label>
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">{t('radius_label')}: {form.service_radius_km} {t('km')}</label>
                <input type="range" min={5} max={50} step={5} value={form.service_radius_km} onChange={e => setForm(f => ({...f, service_radius_km: parseInt(e.target.value)}))} className="w-full accent-pink-600" />
              </div>
              <button type="submit" className="w-full py-2.5 bg-pink-600 text-white rounded-xl text-sm font-semibold hover:bg-pink-700">
                {t('submit_profile')}
              </button>
            </form>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Profile card */}
            <div className="bg-white rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center text-xl">✂️</div>
                <div>
                  <h1 className="font-bold text-gray-800">{profile.name}</h1>
                  <p className="text-sm text-gray-500">{profile.specialty}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${profile.is_active ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'}`}>
                    {profile.is_active ? t('active') : t('pending')}
                  </span>
                </div>
              </div>
              {profile.slug && <Link href={`${prefix}/masters/${profile.slug}`} target="_blank" className="text-xs text-pink-600 hover:underline">{t('view_profile')}</Link>}
            </div>

            {/* Availability */}
            <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
              <button onClick={() => toggle('availability')} className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🗓</span>
                  <span className="text-sm font-medium text-gray-700">{t('availability')}</span>
                </div>
                <span className="text-gray-400 text-sm">{openSection === 'availability' ? '▲' : '▼'}</span>
              </button>
              {openSection === 'availability' && (
                <div className="px-5 pb-5 border-t border-gray-50 pt-4 space-y-2">
                  {avail.map((h, i) => (
                    <div key={h.day_of_week} className={`flex items-center gap-3 ${!h.is_available ? 'opacity-50' : ''}`}>
                      <span className="text-sm text-gray-600 w-20">{DAYS[i]}</span>
                      <input type="time" value={h.start_time||'09:00'} disabled={!h.is_available}
                        onChange={e => setAvail(a => a.map((x,j) => j===i ? {...x, start_time: e.target.value} : x))}
                        className="px-2 py-1 border border-gray-200 rounded-lg text-sm disabled:bg-gray-50" />
                      <span className="text-gray-300">—</span>
                      <input type="time" value={h.end_time||'20:00'} disabled={!h.is_available}
                        onChange={e => setAvail(a => a.map((x,j) => j===i ? {...x, end_time: e.target.value} : x))}
                        className="px-2 py-1 border border-gray-200 rounded-lg text-sm disabled:bg-gray-50" />
                      <label className="flex items-center gap-1.5 ml-auto text-xs text-gray-500 cursor-pointer">
                        <input type="checkbox" checked={h.is_available}
                          onChange={e => setAvail(a => a.map((x,j) => j===i ? {...x, is_available: e.target.checked} : x))}
                          className="accent-pink-600" />
                        Διαθ.
                      </label>
                    </div>
                  ))}
                  <button onClick={saveAvailability} disabled={saving} className="w-full mt-2 py-2 bg-pink-600 text-white rounded-xl text-sm font-medium disabled:opacity-50">
                    {saving ? 'Αποθήκευση...' : 'Αποθήκευση'}
                  </button>
                </div>
              )}
            </div>

            {/* Social links */}
            <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
              <button onClick={() => toggle('social')} className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-2">
                  <span className="text-lg">📱</span>
                  <span className="text-sm font-medium text-gray-700">Social links</span>
                </div>
                <span className="text-gray-400 text-sm">{openSection === 'social' ? '▲' : '▼'}</span>
              </button>
              {openSection === 'social' && (
                <div className="px-5 pb-5 border-t border-gray-50 pt-4 space-y-2">
                  {social.map((s, i) => (
                    <div key={s.platform} className="flex items-center gap-2">
                      <span className="text-sm text-gray-600 w-24 capitalize">{s.platform}</span>
                      <input value={s.url} onChange={e => setSocial(sl => sl.map((x,j) => j===i ? {...x, url: e.target.value} : x))}
                        placeholder={s.platform === 'website' ? 'https://...' : `https://${s.platform}.com/...`}
                        className="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
                    </div>
                  ))}
                  <button onClick={saveSocial} disabled={saving} className="w-full mt-2 py-2 bg-pink-600 text-white rounded-xl text-sm font-medium disabled:opacity-50">
                    {saving ? 'Αποθήκευση...' : 'Αποθήκευση'}
                  </button>
                </div>
              )}
            </div>

            {/* Portfolio — coming soon */}
            <div className="bg-white rounded-2xl border border-gray-100 px-5 py-4 flex items-center gap-2 opacity-60">
              <span className="text-lg">🖼</span>
              <span className="text-sm font-medium text-gray-700">Portfolio</span>
              <span className="ml-auto text-xs text-gray-400">Σύντομα...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
