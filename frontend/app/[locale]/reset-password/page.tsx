'use client';
import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useTranslations } from 'next-intl';

function ResetPasswordForm({ locale }: { locale: string }) {
  const t = useTranslations('reset_password');
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const searchParams = useSearchParams();
  const token = searchParams.get('token') ?? '';

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) setError(t('invalid_token'));
  }, [token]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) { setError(t('mismatch')); return; }
    setError('');
    setLoading(true);
    try {
      const r = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });
      if (r.ok) {
        setDone(true);
      } else {
        const d = await r.json().catch(() => ({}));
        setError(d.detail || t('invalid_token'));
      }
    } catch {
      setError(t('error'));
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm p-8">
        <Link href={prefix || '/'} className="block text-center text-2xl font-bold text-pink-600 mb-6">Lookla</Link>
        {done ? (
          <div className="text-center">
            <div className="text-5xl mb-4">✅</div>
            <h1 className="text-xl font-semibold text-gray-800 mb-3">{t('success_title')}</h1>
            <p className="text-sm text-gray-500 mb-6">{t('success_desc')}</p>
            <Link href={`${prefix}/login`}
              className="inline-block w-full py-3 bg-pink-600 text-white rounded-xl text-base font-semibold text-center hover:bg-pink-700">
              {t('login')}
            </Link>
          </div>
        ) : (
          <>
            <h1 className="text-xl font-semibold text-gray-800 mb-2 text-center">{t('title')}</h1>
            <p className="text-sm text-gray-500 mb-6 text-center">{t('desc')}</p>
            <form onSubmit={submit} className="space-y-3">
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                placeholder={t('new_password')} required minLength={8} autoComplete="new-password"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-base focus:outline-none focus:ring-2 focus:ring-pink-200" />
              <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)}
                placeholder={t('confirm_password')} required minLength={8} autoComplete="new-password"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-base focus:outline-none focus:ring-2 focus:ring-pink-200" />
              {error && <p className="text-sm text-red-500">{error}</p>}
              <button type="submit" disabled={loading || !token}
                className="w-full py-3 bg-pink-600 text-white rounded-xl text-base font-semibold hover:bg-pink-700 disabled:opacity-50">
                {loading ? t('loading') : t('submit')}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

export default function ResetPasswordPage({ params }: { params: { locale: string } }) {
  const locale = (params as any).locale ?? 'el';
  return (
    <Suspense>
      <ResetPasswordForm locale={locale} />
    </Suspense>
  );
}
