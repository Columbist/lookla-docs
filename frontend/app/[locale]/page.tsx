import { useTranslations } from 'next-intl';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import Link from 'next/link';
import { api } from '@/lib/api';
import SearchBar from '@/components/SearchBar';
import CategoryGrid from '@/components/CategoryGrid';
import CityGrid from '@/components/CityGrid';

export default async function HomePage({
  params,
}: {
  params: { locale: string };
}) {
  const locale = (params as any).locale ?? 'el';
  setRequestLocale(locale);
  const t = await getTranslations({ locale, namespace: 'home' });
  const nt = await getTranslations({ locale, namespace: 'nav' });

  const [cities, categories] = await Promise.all([
    api.cities().catch(() => []),
    api.categories(locale).catch(() => []),
  ]);

  const topCities = cities.slice(0, 12);

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link href={`/${locale}`} className="text-xl font-bold text-pink-600">
            Lookla
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm text-gray-600">
            <Link href={`/${locale}/search`} className="hover:text-pink-600">{nt('salons')}</Link>
            <Link href={`/${locale}/masters`} className="hover:text-pink-600">{nt('masters')}</Link>
          </nav>
          <div className="flex items-center gap-2">
            <Link href={`/${locale}/login`} className="text-sm text-gray-600 hover:text-pink-600 px-3 py-1.5">{nt('login')}</Link>
            <Link href={`/${locale}/register`} className="text-sm bg-pink-600 text-white px-3 py-1.5 rounded-lg hover:bg-pink-700">{nt('register')}</Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-br from-pink-50 to-purple-50 py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
            {t('hero_title')}
          </h1>
          <p className="text-gray-500 mb-8">{t('hero_subtitle')}</p>
          <SearchBar locale={locale} />
        </div>
      </section>

      {/* Categories */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        <h2 className="text-xl font-semibold text-gray-800 mb-6">{t('popular_services')}</h2>
        <CategoryGrid categories={categories} locale={locale} />
      </section>

      {/* Cities */}
      <section className="bg-gray-50 py-12">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">{t('popular_cities')}</h2>
          <CityGrid cities={topCities} locale={locale} />
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        <h2 className="text-xl font-semibold text-gray-800 mb-8">{t('how_it_works')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { icon: '🔍', title: t('step_search_title'), desc: t('step_search_desc') },
            { icon: '📅', title: t('step_book_title'), desc: t('step_book_desc') },
            { icon: '✨', title: t('step_enjoy_title'), desc: t('step_enjoy_desc') },
          ].map(item => (
            <div key={item.icon} className="text-center">
              <div className="text-4xl mb-3">{item.icon}</div>
              <h3 className="font-semibold text-gray-800 mb-2">{item.title}</h3>
              <p className="text-gray-500 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 mt-8">
        <div className="max-w-6xl mx-auto px-4 text-center text-sm text-gray-400">
          © 2026 Lookla — Beauty Marketplace Greece
          <div className="flex justify-center gap-4 mt-2">
            {['el','en','ru','uk'].map(l => (
              <Link key={l} href={l === 'el' ? '/' : `/${l}`} className={`uppercase ${l === locale ? 'text-pink-600 font-medium' : 'hover:text-gray-600'}`}>{l}</Link>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
