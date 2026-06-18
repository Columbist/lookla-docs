'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

const SPECIALTIES = ['Nail technician','Makeup artist','Hair colorist','Lash & brow artist','Massage therapist','Hair stylist','Barber','Tattoo artist'];
const DAYS_EL = ['Δευτ','Τρίτ','Τετ','Πέμπ','Παρ','Σάββ','Κυρ'];

export default function MasterDashboard() {
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [form, setForm] = useState({ name:'', specialty:'', bio_el:'', phone:'', base_city:'', service_radius_km:15, does_home_visits:true, has_home_studio:false });
  const [step, setStep] = useState<'loading'|'create'|'profile'>('loading');

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' }).then(r => r.ok ? r.json() : null).then(d => { if (!d) router.push('/login'); });
    fetch('/api/masters/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) { setProfile(d); setStep('profile'); } else setStep('create'); });
  }, []);

  const createProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    const r = await fetch('/api/masters/register', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    if (r.ok) { const d = await r.json(); setProfile(d); setStep('profile'); }
    else alert('Σφάλμα δημιουργίας προφίλ');
  };

  if (step === 'loading') return <div className="min-h-screen flex items-center justify-center"><p className="text-gray-400">Φόρτωση...</p></div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-pink-600">Lookla</Link>
          <span className="text-sm text-gray-600">Προφίλ μάστερ</span>
        </div>
      </header>
      <div className="max-w-2xl mx-auto px-4 py-8">
        {step === 'create' ? (
          <div className="bg-white rounded-2xl p-6">
            <h1 className="text-xl font-bold text-gray-800 mb-2">Δημιουργία προφίλ επαγγελματία</h1>
            <p className="text-sm text-gray-500 mb-6">Το προφίλ σας θα εμφανιστεί μετά από έλεγχο (1-24 ώρες)</p>
            <form onSubmit={createProfile} className="space-y-4">
              <input required placeholder="Ονοματεπώνυμο *" value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))} className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              <select required value={form.specialty} onChange={e => setForm(f => ({...f, specialty: e.target.value}))} className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-700">
                <option value="">Ειδικότητα *</option>
                {SPECIALTIES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <textarea placeholder="Βιογραφικό (ελληνικά)" value={form.bio_el} onChange={e => setForm(f => ({...f, bio_el: e.target.value}))} className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm h-24 resize-none focus:outline-none focus:ring-2 focus:ring-pink-200" />
              <input placeholder="Τηλέφωνο" value={form.phone} onChange={e => setForm(f => ({...f, phone: e.target.value}))} className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              <input placeholder="Πόλη βάσης" value={form.base_city} onChange={e => setForm(f => ({...f, base_city: e.target.value}))} className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input type="checkbox" checked={form.does_home_visits} onChange={e => setForm(f => ({...f, does_home_visits: e.target.checked}))} className="accent-pink-600" />
                  Κατ' οίκον επισκέψεις
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input type="checkbox" checked={form.has_home_studio} onChange={e => setForm(f => ({...f, has_home_studio: e.target.checked}))} className="accent-pink-600" />
                  Studio στο σπίτι
                </label>
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Ακτίνα εξυπηρέτησης: {form.service_radius_km} χλμ</label>
                <input type="range" min={5} max={50} step={5} value={form.service_radius_km} onChange={e => setForm(f => ({...f, service_radius_km: parseInt(e.target.value)}))} className="w-full accent-pink-600" />
              </div>
              <button type="submit" className="w-full py-2.5 bg-pink-600 text-white rounded-xl text-sm font-semibold hover:bg-pink-700">
                Υποβολή προφίλ
              </button>
            </form>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center text-xl">✂️</div>
                <div>
                  <h1 className="font-bold text-gray-800">{profile.name}</h1>
                  <p className="text-sm text-gray-500">{profile.specialty}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${profile.is_active ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'}`}>
                    {profile.is_active ? '✓ Ενεργό' : '⏳ Υπό έλεγχο'}
                  </span>
                </div>
              </div>
              {profile.slug && <Link href={`/masters/${profile.slug}`} target="_blank" className="text-xs text-pink-600 hover:underline">Δείτε το δημόσιο προφίλ σας →</Link>}
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                {icon:'🖼', label:'Portfolio', href:'#'},
                {icon:'🗓', label:'Διαθεσιμότητα', href:'#'},
                {icon:'💶', label:'Υπηρεσίες', href:'#'},
                {icon:'📱', label:'Social links', href:'#'},
              ].map(item => (
                <a key={item.label} href={item.href} className="bg-white rounded-xl p-4 flex items-center gap-2 border border-gray-100 hover:shadow-sm transition-shadow">
                  <span className="text-xl">{item.icon}</span>
                  <span className="text-sm font-medium text-gray-700">{item.label}</span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
