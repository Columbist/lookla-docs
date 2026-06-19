'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import LanguageSwitcher from '@/components/LanguageSwitcher';

const T: Record<string, Record<string, string>> = {
  el: {
    title: 'Ελεύθεροι Επαγγελματίες',
    subtitle: 'Μαέστροι ομορφιάς που έρχονται σε εσάς ή δέχονται στο σπίτι τους',
    salons: 'Κομμωτήρια & Σαλόνια',
    masters: 'Ελεύθεροι Επαγγελματίες',
    login: 'Σύνδεση',
    register: 'Εγγραφή',
    search_placeholder: 'Υπηρεσία ή τοποθεσία...',
    empty_title: 'Σύντομα διαθέσιμο',
    empty_desc: 'Οι πρώτοι ελεύθεροι επαγγελματίες ομορφιάς έρχονται σύντομα στην πλατφόρμα μας.',
    cta: 'Είστε επαγγελματίας ομορφιάς;',
    cta_desc: 'Δημιουργήστε το προφίλ σας δωρεάν και αποκτήστε νέους πελάτες.',
    cta_btn: 'Εγγραφείτε ως επαγγελματίας',
    home_visits: 'Εξυπηρέτηση κατ\' οίκον',
    home_studio: 'Ιδιωτικό στούντιο',
  },
  en: {
    title: 'Independent Professionals',
    subtitle: 'Beauty experts who come to you or welcome you at their home studio',
    salons: 'Salons & Studios',
    masters: 'Independent Professionals',
    login: 'Log in',
    register: 'Sign up',
    search_placeholder: 'Service or location...',
    empty_title: 'Coming soon',
    empty_desc: 'The first independent beauty professionals are coming to our platform soon.',
    cta: 'Are you a beauty professional?',
    cta_desc: 'Create your free profile and reach new clients.',
    cta_btn: 'Join as a professional',
    home_visits: 'Home visits',
    home_studio: 'Private studio',
  },
  ru: {
    title: 'Независимые Мастера',
    subtitle: 'Мастера красоты, которые приедут к вам или примут в своей студии',
    salons: 'Салоны красоты',
    masters: 'Мастера',
    login: 'Войти',
    register: 'Регистрация',
    search_placeholder: 'Услуга или город...',
    empty_title: 'Скоро появятся',
    empty_desc: 'Первые независимые мастера красоты скоро появятся на нашей платформе.',
    cta: 'Вы мастер красоты?',
    cta_desc: 'Создайте бесплатный профиль и привлекайте новых клиентов.',
    cta_btn: 'Зарегистрироваться как мастер',
    home_visits: 'Выезд на дом',
    home_studio: 'Домашняя студия',
  },
  uk: {
    title: 'Незалежні Майстри',
    subtitle: 'Майстри краси, які приїдуть до вас або приймуть у своїй студії',
    salons: 'Салони краси',
    masters: 'Майстри',
    login: 'Увійти',
    register: 'Реєстрація',
    search_placeholder: 'Послуга або місто...',
    empty_title: 'Незабаром',
    empty_desc: 'Перші незалежні майстри краси незабаром з\'являться на нашій платформі.',
    cta: 'Ви майстер краси?',
    cta_desc: 'Створіть безкоштовний профіль і залучайте нових клієнтів.',
    cta_btn: 'Зареєструватися як майстер',
    home_visits: 'Виїзд додому',
    home_studio: 'Домашня студія',
  },
};

const SPECIALTIES: Record<string, string[]> = {
  el: ['Κομμωτής / Κομμώτρια', 'Τεχνίτης Νυχιών', 'Αισθητικός', 'Μακιγιέρ', 'Εξειδικευμένος Αποτρίχωσης', 'Τεχνίτης Βλεφαρίδων', 'Μασέρ / Μασέζ', 'Τατουάζ & Piercing'],
  en: ['Hairstylist', 'Nail Technician', 'Esthetician', 'Makeup Artist', 'Waxing Specialist', 'Lash Technician', 'Massage Therapist', 'Tattoo & Piercing Artist'],
  ru: ['Парикмахер', 'Мастер маникюра', 'Косметолог', 'Визажист', 'Специалист по эпиляции', 'Мастер ресниц', 'Массажист', 'Тату & Пирсинг'],
  uk: ['Перукар', 'Майстер манікюру', 'Косметолог', 'Візажист', 'Спеціаліст з епіляції', 'Майстер вій', 'Масажист', 'Тату & Пірсинг'],
};

export default function MastersPage({ params }: { params: { locale: string } }) {
  const locale = (params as any).locale ?? 'el';
  const t = T[locale] || T.en;
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const specialties = SPECIALTIES[locale] || SPECIALTIES.en;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link href={prefix || '/'} className="text-xl font-bold text-pink-600">Lookla</Link>
          <nav className="hidden md:flex items-center gap-6 text-sm text-gray-600">
            <Link href={`${prefix}/search`} className="hover:text-pink-600">{t.salons}</Link>
            <Link href={`${prefix}/masters`} className="text-pink-600 font-medium">{t.masters}</Link>
          </nav>
          <div className="flex items-center gap-2">
            <Link href={`${prefix}/login`} className="text-sm text-gray-600 hover:text-pink-600 px-3 py-1.5">{t.login}</Link>
            <Link href={`${prefix}/register`} className="text-sm bg-pink-600 text-white px-3 py-1.5 rounded-lg hover:bg-pink-700">{t.register}</Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-br from-purple-50 to-pink-50 py-12 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">{t.title}</h1>
          <p className="text-gray-500 mb-6">{t.subtitle}</p>
          <div className="flex flex-wrap justify-center gap-2">
            {[
              { icon: '🏠', label: t.home_visits },
              { icon: '🎨', label: t.home_studio },
            ].map(b => (
              <span key={b.label} className="flex items-center gap-1.5 bg-white border border-pink-100 text-sm text-gray-600 px-3 py-1.5 rounded-full">
                {b.icon} {b.label}
              </span>
            ))}
          </div>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Specialties filter */}
        <div className="flex flex-wrap gap-2 mb-10">
          {specialties.map(s => (
            <button key={s} className="text-sm px-3 py-1.5 rounded-full border border-gray-200 text-gray-600 hover:border-pink-300 hover:text-pink-600 transition-colors bg-white">
              {s}
            </button>
          ))}
        </div>

        {/* Empty state */}
        <div className="text-center py-20">
          <p className="text-6xl mb-5">💅</p>
          <h2 className="text-xl font-bold text-gray-800 mb-3">{t.empty_title}</h2>
          <p className="text-gray-500 text-sm max-w-md mx-auto mb-10">{t.empty_desc}</p>

          {/* CTA for professionals */}
          <div className="bg-white border border-pink-100 rounded-2xl p-8 max-w-md mx-auto">
            <p className="font-semibold text-gray-800 mb-2">{t.cta}</p>
            <p className="text-sm text-gray-500 mb-5">{t.cta_desc}</p>
            <Link
              href={`${prefix}/register?role=professional`}
              className="block w-full py-3 bg-pink-600 text-white rounded-xl text-sm font-semibold hover:bg-pink-700 text-center"
            >
              {t.cta_btn}
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8">
        <div className="max-w-6xl mx-auto px-4 text-center text-sm text-gray-400">
          © 2026 Lookla — Beauty Marketplace Greece
          <LanguageSwitcher currentLocale={locale} />
        </div>
      </footer>
    </div>
  );
}
