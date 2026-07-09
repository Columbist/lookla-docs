'use client';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';

export default function NotFound() {
  const t = useTranslations('common');
  const locale = useLocale();
  const prefix = locale === 'el' ? '' : `/${locale}`;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <p className="text-6xl mb-4">💇</p>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">404</h1>
        <p className="text-gray-500 mb-6">{t('not_found_title')}</p>
        <Link href={prefix || '/'} className="px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700">
          {t('home')}
        </Link>
      </div>
    </div>
  );
}
