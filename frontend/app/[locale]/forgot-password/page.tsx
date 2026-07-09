'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';

export default function ForgotPasswordPage({ params }: { params: { locale: string } }) {
  const locale = (params as any).locale ?? 'el';
  const t = useTranslations('forgot_password');
  const prefix = locale === 'el' ? '' : `/${locale}`;

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    }).catch(() => {});
    setLoading(false);
    setSent(true);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm p-8">
        <Link href={prefix || '/'} className="block text-center text-2xl font-bold text-pink-600 mb-6">Lookla</Link>
        {sent ? (
          <div className="text-center">
            <div className="text-5xl mb-4">📬</div>
            <h1 className="text-xl font-semibold text-gray-800 mb-3">{t('success_title')}</h1>
            <p className="text-sm text-gray-500 mb-6">{t('success_desc')}</p>
            <Link href={`${prefix}/login`} className="text-pink-600 font-medium text-sm hover:underline">{t('back')}</Link>
          </div>
        ) : (
          <>
            <h1 className="text-xl font-semibold text-gray-800 mb-2 text-center">{t('title')}</h1>
            <p className="text-sm text-gray-500 mb-6 text-center">{t('desc')}</p>
            <form onSubmit={submit} className="space-y-3">
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                placeholder="Email" required autoComplete="email"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-base focus:outline-none focus:ring-2 focus:ring-pink-200" />
              <button type="submit" disabled={loading}
                className="w-full py-3 bg-pink-600 text-white rounded-xl text-base font-semibold hover:bg-pink-700 disabled:opacity-50">
                {loading ? t('loading') : t('submit')}
              </button>
            </form>
            <div className="mt-4 text-center">
              <Link href={`${prefix}/login`} className="text-sm text-gray-500 hover:text-pink-600">{t('back')}</Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
