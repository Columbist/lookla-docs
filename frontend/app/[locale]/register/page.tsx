'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const LANGS = [
  { code: 'el', label: 'Ελληνικά' },
  { code: 'en', label: 'English' },
  { code: 'ru', label: 'Русский' },
  { code: 'uk', label: 'Українська' },
];

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: '', password: '', name: '', preferred_language: 'el', website_url: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [generatedPass, setGeneratedPass] = useState('');

  const generatePassword = async () => {
    const r = await fetch('/api/auth/generate-password');
    const d = await r.json();
    setGeneratedPass(d.password);
    setForm(f => ({ ...f, password: d.password }));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError('');
    const r = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(form),
    });
    setLoading(false);
    if (r.ok) {
      router.push('/account');
    } else {
      const d = await r.json().catch(() => ({}));
      setError(d.detail || 'Σφάλμα εγγραφής');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm p-8">
        <Link href="/" className="block text-center text-2xl font-bold text-pink-600 mb-6">Lookla</Link>
        <h1 className="text-xl font-semibold text-gray-800 mb-6 text-center">Εγγραφή</h1>

        <a href="/api/auth/google/start"
           className="flex items-center justify-center gap-2 w-full py-2.5 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50 mb-4">
          <img src="https://www.google.com/favicon.ico" className="w-4 h-4" alt="" />
          Εγγραφή με Google
        </a>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-gray-100" />
          <span className="text-xs text-gray-400">ή</span>
          <div className="flex-1 h-px bg-gray-100" />
        </div>

        <form onSubmit={submit} className="space-y-3">
          {/* Honeypot */}
          <input name="website_url" value={form.website_url} onChange={e => setForm(f => ({...f, website_url: e.target.value}))} style={{display:'none'}} tabIndex={-1} />

          <input type="text" placeholder="Ονοματεπώνυμο" value={form.name}
            onChange={e => setForm(f => ({...f, name: e.target.value}))}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />

          <input type="email" placeholder="Email" required value={form.email}
            onChange={e => setForm(f => ({...f, email: e.target.value}))}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />

          <div className="relative">
            <input type="text" placeholder="Κωδικός" required value={form.password}
              onChange={e => setForm(f => ({...f, password: e.target.value}))}
              className="w-full px-4 py-2.5 pr-28 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
            <button type="button" onClick={generatePassword}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-pink-600 hover:text-pink-700 font-medium whitespace-nowrap">
              Προτεινόμενος
            </button>
          </div>
          {generatedPass && (
            <p className="text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2">
              💡 Αποθηκεύστε: <strong>{generatedPass}</strong>
            </p>
          )}

          <select value={form.preferred_language} onChange={e => setForm(f => ({...f, preferred_language: e.target.value}))}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-pink-200">
            {LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
          </select>

          {error && <p className="text-xs text-red-500">{error}</p>}

          <button type="submit" disabled={loading}
            className="w-full py-2.5 bg-pink-600 text-white rounded-xl text-sm font-semibold hover:bg-pink-700 disabled:opacity-50">
            {loading ? 'Φόρτωση...' : 'Εγγραφή'}
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-gray-500">
          Έχετε ήδη λογαριασμό; <Link href="/login" className="text-pink-600 font-medium">Σύνδεση</Link>
        </p>
      </div>
    </div>
  );
}
