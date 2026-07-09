'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';

interface Me { id: number; email: string; name?: string; role: string; preferred_language: string; is_email_verified: boolean; }

export default function AccountPage() {
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations('account');
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { setUser(d); setLoading(false); if (!d) router.push(`${prefix}/login`); })
      .catch(() => { setLoading(false); router.push(`${prefix}/login`); });
  }, []);

  const logout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    router.push(prefix || '/');
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="text-gray-400">{t('loading')}</div></div>;
  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link href={prefix || '/'} className="text-xl font-bold text-pink-600">Lookla</Link>
          <button onClick={logout} className="text-sm text-gray-500 hover:text-red-500">{t('logout')}</button>
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
                  {user.is_email_verified ? t('verified') : t('not_verified')}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {[
            { href: `${prefix}/account/bookings`, icon: '📅', label: t('bookings') },
            { href: `${prefix}/account/messages`, icon: '✉️', label: t('messages') },
            { href: `${prefix}/account/favorites`, icon: '❤️', label: t('favorites') },
            { href: `${prefix}/account/settings`, icon: '⚙️', label: t('settings') },
          ].map(item => (
            <Link key={item.href} href={item.href}
              className="bg-white rounded-xl p-4 flex items-center gap-3 hover:shadow-sm transition-shadow border border-gray-50">
              <span className="text-2xl">{item.icon}</span>
              <span className="text-sm font-medium text-gray-700">{item.label}</span>
            </Link>
          ))}
        </div>

        {user.role === 'salon_owner' && (
          <Link href={`${prefix}/dashboard/salon`} className="mt-3 flex items-center gap-3 bg-pink-50 border border-pink-100 rounded-xl p-4 hover:bg-pink-100 transition-colors">
            <span className="text-2xl">💼</span>
            <span className="text-sm font-medium text-pink-700">{t('manage_salon')}</span>
          </Link>
        )}
      </div>
    </div>
  );
}
