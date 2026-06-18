'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface Me { id: number; email: string; name?: string; role: string; preferred_language: string; is_email_verified: boolean; }

export default function AccountPage() {
  const router = useRouter();
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { setUser(d); setLoading(false); if (!d) router.push('/login'); })
      .catch(() => { setLoading(false); router.push('/login'); });
  }, []);

  const logout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    router.push('/');
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="text-gray-400">Φόρτωση...</div></div>;
  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-pink-600">Lookla</Link>
          <button onClick={logout} className="text-sm text-gray-500 hover:text-red-500">Αποσύνδεση</button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl p-6 mb-4">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 bg-pink-100 rounded-full flex items-center justify-center text-2xl">
              {user.name ? user.name[0].toUpperCase() : '👤'}
            </div>
            <div>
              <h1 className="font-semibold text-gray-800">{user.name || user.email}</h1>
              <p className="text-sm text-gray-500">{user.email}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-xs px-2 py-0.5 rounded-full ${user.is_email_verified ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'}`}>
                  {user.is_email_verified ? '✓ Επαληθευμένο' : '⚠ Μη επαληθευμένο email'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {[
            { href: '/account/bookings', icon: '📅', label: 'Κρατήσεις μου' },
            { href: '/account/messages', icon: '✉️', label: 'Μηνύματα' },
            { href: '/account/favorites', icon: '❤️', label: 'Αγαπημένα' },
            { href: '/account/settings', icon: '⚙️', label: 'Ρυθμίσεις' },
          ].map(item => (
            <Link key={item.href} href={item.href}
              className="bg-white rounded-xl p-4 flex items-center gap-3 hover:shadow-sm transition-shadow border border-gray-50">
              <span className="text-2xl">{item.icon}</span>
              <span className="text-sm font-medium text-gray-700">{item.label}</span>
            </Link>
          ))}
        </div>

        {user.role === 'salon_owner' && (
          <Link href="/dashboard/salon" className="mt-3 flex items-center gap-3 bg-pink-50 border border-pink-100 rounded-xl p-4 hover:bg-pink-100 transition-colors">
            <span className="text-2xl">💼</span>
            <span className="text-sm font-medium text-pink-700">Διαχείριση σαλονιού</span>
          </Link>
        )}
      </div>
    </div>
  );
}
