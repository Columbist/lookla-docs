'use client';
import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import type { SalonListItem, City, Category } from '@/lib/api';
import SalonCard from '@/components/SalonCard';
import dynamic from 'next/dynamic';

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false });

// i18n strings inline (avoids next-intl server issues in search page)
const T: Record<string, Record<string, string>> = {
  el: { results: 'αποτελέσματα', list: '☰ Λίστα', map: '🗺 Χάρτης', all_cities: 'Πόλη', all_cats: 'Κατηγορία', no_results: 'Δεν βρέθηκαν αποτελέσματα', placeholder: 'Αναζήτηση...' },
  en: { results: 'results', list: '☰ List', map: '🗺 Map', all_cities: 'City', all_cats: 'Category', no_results: 'No results found', placeholder: 'Search...' },
  ru: { results: 'результатов', list: '☰ Список', map: '🗺 Карта', all_cities: 'Город', all_cats: 'Категория', no_results: 'Ничего не найдено', placeholder: 'Поиск...' },
  uk: { results: 'результатів', list: '☰ Список', map: '🗺 Карта', all_cities: 'Місто', all_cats: 'Категорія', no_results: 'Нічого не знайдено', placeholder: 'Пошук...' },
};

function SearchContent({ locale }: { locale: string }) {
  const sp = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const t = T[locale] || T.el;

  const city = sp.get('city') || '';
  const category = sp.get('category') || '';
  const q = sp.get('q') || '';
  const view = sp.get('view') || 'list';

  const [salons, setSalons] = useState<SalonListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [cities, setCities] = useState<City[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/cities`).then(r => r.json()).then(setCities).catch(() => []);
    fetch(`/api/categories?lang=${locale}`).then(r => r.json()).then(setCategories).catch(() => []);
  }, [locale]);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({ limit: '24' });
    if (city) params.set('city', city);
    if (q) params.set('q', q);
    fetch(`/api/salons?${params}`)
      .then(r => r.json())
      .then(d => { setSalons(d.items || []); setTotal(d.total || 0); })
      .catch(() => { setSalons([]); setTotal(0); })
      .finally(() => setLoading(false));
  }, [city, q, category]);

  const update = (key: string, value: string) => {
    const p = new URLSearchParams(sp.toString());
    if (value) p.set(key, value); else p.delete(key);
    router.push(`${pathname}?${p}`);
  };

  const prefix = locale === 'el' ? '' : `/${locale}`;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-100 px-4 py-3 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto flex items-center gap-3 flex-wrap">
          <Link href={`${prefix}/`} className="text-xl font-bold text-pink-600 shrink-0">Lookla</Link>

          <input type="text" defaultValue={q} placeholder={t.placeholder}
            onKeyDown={e => e.key === 'Enter' && update('q', (e.target as HTMLInputElement).value)}
            className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-pink-300 w-36" />

          <select value={city} onChange={e => update('city', e.target.value)}
            className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-gray-700">
            <option value="">{t.all_cities}</option>
            {cities.slice(0, 20).map(c => <option key={c.city} value={c.city}>{c.city} ({c.count})</option>)}
          </select>

          <select value={category} onChange={e => update('category', e.target.value)}
            className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-gray-700">
            <option value="">{t.all_cats}</option>
            {categories.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}
          </select>

          <div className="ml-auto flex items-center gap-1.5 shrink-0">
            <button onClick={() => update('view', 'list')}
              className={`px-3 py-1.5 rounded-lg text-sm ${view !== 'map' ? 'bg-pink-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              {t.list}
            </button>
            <button onClick={() => update('view', 'map')}
              className={`px-3 py-1.5 rounded-lg text-sm ${view === 'map' ? 'bg-pink-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              {t.map}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <p className="text-sm text-gray-500 mb-4">
          {loading ? '...' : `${total} ${t.results}`}
          {city && <span className="ml-1 font-medium text-gray-700">— {city}</span>}
        </p>

        {view === 'map' ? (
          <MapView salons={salons} locale={locale} />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {loading ? (
              Array.from({length: 6}).map((_, i) => (
                <div key={i} className="bg-white rounded-xl h-64 animate-pulse border border-gray-100" />
              ))
            ) : salons.length > 0 ? (
              salons.map(salon => <SalonCard key={salon.id} salon={salon} locale={locale} />)
            ) : (
              <div className="col-span-3 text-center py-16 text-gray-400">{t.no_results}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage({ params }: { params: { locale: string } }) {
  const locale = (params as any).locale ?? 'el';
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50 flex items-center justify-center"><div className="text-gray-400">Φόρτωση...</div></div>}>
      <SearchContent locale={locale} />
    </Suspense>
  );
}
