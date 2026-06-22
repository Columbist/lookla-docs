import { getTranslations, setRequestLocale } from 'next-intl/server';
import { api } from '@/lib/api';
import SearchBar from '@/components/SearchBar';
import CategoryGrid from '@/components/CategoryGrid';
import CityGrid from '@/components/CityGrid';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import Header from '@/components/Header';

export default async function HomePage({
  params,
}: {
  params: { locale: string };
}) {
  const locale = (params as any).locale ?? 'el';
  setRequestLocale(locale);
  const t = await getTranslations({ locale, namespace: 'home' });

  const [cities, categories] = await Promise.all([
    api.cities().catch(() => []),
    api.categories(locale).catch(() => []),
  ]);

  const topCities = cities.slice(0, 12);

  return (
    <div className="min-h-screen bg-white">
      <Header locale={locale} />

      {/* Hero */}
      <section className="bg-gradient-to-br from-pink-50 to-purple-50 py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4 leading-tight">
            {t('hero_title')}
          </h1>
          <p className="text-lg text-gray-500 mb-8">{t('hero_subtitle')}</p>
          <SearchBar locale={locale} />
        </div>
      </section>

      {/* Categories */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">{t('popular_services')}</h2>
        <CategoryGrid categories={categories} locale={locale} />
      </section>

      {/* Cities */}
      <section className="bg-gray-50 py-12">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">{t('popular_cities')}</h2>
          <CityGrid cities={topCities} locale={locale} />
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold text-gray-800 mb-10">{t('how_it_works')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {[
            { icon: '🔍', title: t('step_search_title'), desc: t('step_search_desc') },
            { icon: '📅', title: t('step_book_title'), desc: t('step_book_desc') },
            { icon: '✨', title: t('step_enjoy_title'), desc: t('step_enjoy_desc') },
          ].map(item => (
            <div key={item.icon} className="text-center">
              <div className="text-5xl mb-4">{item.icon}</div>
              <h3 className="text-lg font-bold text-gray-800 mb-2">{item.title}</h3>
              <p className="text-base text-gray-500">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 mt-8">
        <div className="max-w-6xl mx-auto px-4 text-center text-sm text-gray-400">
          © 2026 Lookla — Beauty Marketplace Greece
          <LanguageSwitcher currentLocale={locale} />
        </div>
      </footer>
    </div>
  );
}
