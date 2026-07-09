'use client';
import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useTranslations, useLocale } from 'next-intl';

function VerifyContent() {
  const t = useTranslations('verify_email');
  const locale = useLocale();
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const sp = useSearchParams();
  const token = sp.get('token') ?? '';

  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');

  useEffect(() => {
    if (!token) { setStatus('error'); return; }
    fetch('/api/auth/verify-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    })
      .then(r => setStatus(r.ok ? 'ok' : 'error'))
      .catch(() => setStatus('error'));
  }, [token]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm p-8 text-center">
        <Link href={prefix || '/'} className="block text-2xl font-bold text-pink-600 mb-6">Lookla</Link>
        {status === 'loading' && (
          <>
            <div className="text-4xl mb-4 animate-pulse">📧</div>
            <p className="text-gray-500">{t('loading')}</p>
          </>
        )}
        {status === 'ok' && (
          <>
            <div className="text-5xl mb-4">✅</div>
            <h1 className="text-xl font-semibold text-gray-800 mb-2">{t('success_title')}</h1>
            <p className="text-sm text-gray-500 mb-6">{t('success_desc')}</p>
            <Link href={`${prefix}/account`}
              className="block w-full py-3 bg-pink-600 text-white rounded-xl text-base font-semibold hover:bg-pink-700">
              {t('go_account')}
            </Link>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="text-5xl mb-4">❌</div>
            <h1 className="text-xl font-semibold text-gray-800 mb-2">{t('error_title')}</h1>
            <p className="text-sm text-gray-500 mb-6">{t('error_desc')}</p>
            <Link href={`${prefix}/login`}
              className="block w-full py-3 border border-pink-200 text-pink-600 rounded-xl text-base font-semibold hover:bg-pink-50">
              {t('go_login')}
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyContent />
    </Suspense>
  );
}
