import { getTranslations } from 'next-intl/server';
import { api } from '@/lib/api';
import SalonCard from '@/components/SalonCard';
import SearchFilters from '@/components/SearchFilters';
import MapView from '@/components/MapView';

interface Props {
  params: { locale: string };
  searchParams: { q?: string; city?: string; category?: string; view?: string };
}

export default async function SearchPage({ params, searchParams }: Props) {
  const { locale } = await params;
  const sp = await searchParams;
  const t = await getTranslations('search');
  const isMap = sp.view === 'map';

  const [salonsData, cities, categories] = await Promise.all([
    api.salons.list({
      limit: 24,
      ...(sp.city ? { city: sp.city } : {}),
    }).catch(() => ({ items: [], total: 0, page: 1, limit: 24, pages: 0 })),
    api.cities().catch(() => []),
    api.categories(locale).catch(() => []),
  ]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-100 px-4 py-3 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto flex items-center gap-4">
          <a href={`/${locale}`} className="text-xl font-bold text-pink-600 mr-2">Lookla</a>
          <SearchFilters locale={locale} cities={cities} categories={categories} current={sp} />
          <div className="ml-auto flex items-center gap-2">
            <a href={`?${new URLSearchParams({...sp, view: 'list'})}`}
               className={`px-3 py-1.5 rounded-lg text-sm ${!isMap ? 'bg-pink-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              ☰ {t('list_view')}
            </a>
            <a href={`?${new URLSearchParams({...sp, view: 'map'})}`}
               className={`px-3 py-1.5 rounded-lg text-sm ${isMap ? 'bg-pink-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              🗺 {t('map_view')}
            </a>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <p className="text-sm text-gray-500 mb-4">
          {t('results_count', { count: salonsData.total })}
          {sp.city && <span className="ml-1 font-medium text-gray-700">— {sp.city}</span>}
        </p>

        {isMap ? (
          <MapView salons={salonsData.items} locale={locale} />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {salonsData.items.map(salon => (
              <SalonCard key={salon.id} salon={salon} locale={locale} />
            ))}
            {salonsData.items.length === 0 && (
              <div className="col-span-3 text-center py-16 text-gray-400">{t('no_results')}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
