'use client';
import { useState } from 'react';
import Link from 'next/link';
import LanguageSwitcher from './LanguageSwitcher';

const T: Record<string, Record<string, string>> = {
  el: { salons: 'Κομμωτήρια & Σαλόνια', masters: 'Ελεύθεροι Επαγγελματίες', login: 'Σύνδεση', register: 'Εγγραφή', pricing: 'Τιμολόγηση' },
  en: { salons: 'Salons & Studios', masters: 'Professionals', login: 'Log in', register: 'Sign up', pricing: 'Pricing' },
  ru: { salons: 'Салоны красоты', masters: 'Мастера', login: 'Войти', register: 'Регистрация', pricing: 'Тарифы' },
  uk: { salons: 'Салони краси', masters: 'Майстри', login: 'Увійти', register: 'Реєстрація', pricing: 'Тарифи' },
};

export default function Header({ locale }: { locale: string }) {
  const t = T[locale] || T.en;
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const [open, setOpen] = useState(false);

  return (
    <header className="bg-white border-b border-gray-100 sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href={prefix || '/'} className="text-xl font-bold text-pink-600">Lookla</Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6 text-sm text-gray-600">
          <Link href={`${prefix}/search`} className="hover:text-pink-600">{t.salons}</Link>
          <Link href={`${prefix}/masters`} className="hover:text-pink-600">{t.masters}</Link>
          <Link href={`${prefix}/pricing`} className="hover:text-pink-600">{t.pricing}</Link>
        </nav>

        {/* Desktop auth */}
        <div className="hidden md:flex items-center gap-2">
          <Link href={`${prefix}/login`} className="text-sm text-gray-600 hover:text-pink-600 px-3 py-1.5">{t.login}</Link>
          <Link href={`${prefix}/register`} className="text-sm bg-pink-600 text-white px-3 py-1.5 rounded-lg hover:bg-pink-700">{t.register}</Link>
        </div>

        {/* Mobile burger */}
        <button onClick={() => setOpen(!open)} className="md:hidden p-2 rounded-lg hover:bg-gray-100" aria-label="Menu">
          {open ? (
            <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden bg-white border-t border-gray-100 px-4 py-4 space-y-1">
          <Link href={`${prefix}/search`} onClick={() => setOpen(false)}
            className="flex items-center gap-3 px-3 py-3 rounded-xl hover:bg-gray-50 text-base text-gray-700">
            💇 {t.salons}
          </Link>
          <Link href={`${prefix}/masters`} onClick={() => setOpen(false)}
            className="flex items-center gap-3 px-3 py-3 rounded-xl hover:bg-gray-50 text-base text-gray-700">
            💅 {t.masters}
          </Link>
          <Link href={`${prefix}/pricing`} onClick={() => setOpen(false)}
            className="flex items-center gap-3 px-3 py-3 rounded-xl hover:bg-gray-50 text-base text-gray-700">
            💳 {t.pricing}
          </Link>
          <div className="pt-3 border-t border-gray-100 flex gap-2">
            <Link href={`${prefix}/login`} onClick={() => setOpen(false)}
              className="flex-1 py-3 text-center border border-pink-200 text-pink-600 rounded-xl text-base font-semibold hover:bg-pink-50">
              {t.login}
            </Link>
            <Link href={`${prefix}/register`} onClick={() => setOpen(false)}
              className="flex-1 py-3 text-center bg-pink-600 text-white rounded-xl text-base font-semibold hover:bg-pink-700">
              {t.register}
            </Link>
          </div>
          <div className="pt-3 flex justify-center">
            <LanguageSwitcher currentLocale={locale} />
          </div>
        </div>
      )}
    </header>
  );
}
