'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function LoginPage({ params }: { params: Promise<{ locale: string }> }) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError('');
    const r = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    });
    setLoading(false);
    if (r.ok) {
      router.push('/account');
    } else {
      const d = await r.json().catch(() => ({}));
      setError(d.detail || 'Λάθος email ή κωδικός');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm p-8">
        <Link href="/" className="block text-center text-2xl font-bold text-pink-600 mb-6">Lookla</Link>
        <h1 className="text-xl font-semibold text-gray-800 mb-6 text-center">Σύνδεση</h1>

        {/* Google OAuth */}
        <a href="/api/auth/google/start"
           className="flex items-center justify-center gap-2 w-full py-2.5 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50 mb-4">
          <img src="https://www.google.com/favicon.ico" className="w-4 h-4" alt="" />
          Σύνδεση με Google
        </a>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-gray-100" />
          <span className="text-xs text-gray-400">ή</span>
          <div className="flex-1 h-px bg-gray-100" />
        </div>

        <form onSubmit={submit} className="space-y-3">
          <input type="email" value={email} onChange={e => setEmail(e.target.value)}
            placeholder="Email" required
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder="Κωδικός" required
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-pink-200" />
          {error && <p className="text-xs text-red-500">{error}</p>}
          <button type="submit" disabled={loading}
            className="w-full py-2.5 bg-pink-600 text-white rounded-xl text-sm font-semibold hover:bg-pink-700 disabled:opacity-50">
            {loading ? 'Φόρτωση...' : 'Σύνδεση'}
          </button>
        </form>

        <div className="mt-4 text-center space-y-2">
          <Link href="/forgot-password" className="text-xs text-gray-500 hover:text-pink-600 block">Ξεχάσατε τον κωδικό;</Link>
          <p className="text-xs text-gray-500">Δεν έχετε λογαριασμό; <Link href="/register" className="text-pink-600 font-medium">Εγγραφή</Link></p>
        </div>
      </div>
    </div>
  );
}
