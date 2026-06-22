'use client';
import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import type { SalonListItem, City, Category } from '@/lib/api';
import SalonCard from '@/components/SalonCard';
import dynamic from 'next/dynamic';

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false });

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
  const inputRef = useRef<HTMLInputElement>(null);

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
    if (category) params.set('category', category); // FIX: was missing
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

  const doSearch = () => {
    update('q', inputRef.current?.value || '');
  };

  const prefix = locale === 'el' ? '' : `/${locale}`;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-100 px-4 py-3 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center gap-2">
          <Link href={prefix || '/'} className="text-xl font-bold text-pink-600 shrink-0 mr-1">Lookla</Link>

          {/* Search input */}
          <div className="flex items-center border border-gray-200 rounded-lg overflow-hidden flex-1 min-w-[160px] max-w-xs">
            <input
              ref={inputRef}
              type="text"
              defaultValue={q}
              placeholder={t.placeholder}
              onKeyDown={e => e.key === 'Enter' && doSearch()}
              className="px-3 py-2 text-sm focus:outline-none flex-1 min-w-0"
            />
            <button onClick={doSearch} className="px-3 py-2 bg-pink-600 text-white text-sm font-medium hover:bg-pink-700 shrink-0">
              🔍
            </button>
          </div>

          {/* City filter */}
          <select value={city} onChange={e => update('city', e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-700 bg-white">
            <option value="">{t.all_cities}</option>
            {cities.slice(0, 30).map(c => <option key={c.city} value={c.city}>{c.city} ({c.count})</option>)}
          </select>

          {/* Category filter */}
          <select value={category} onChange={e => update('category', e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-700 bg-white">
            <option value="">{t.all_cats}</option>
            {categories.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}
          </select>

          {/* View toggle */}
          <div className="ml-auto flex items-center gap-1 shrink-0">
            <button onClick={() => update('view', 'list')}
              className={`px-3 py-2 rounded-lg text-sm font-medium ${view !== 'map' ? 'bg-pink-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              {t.list}
            </button>
            <button onClick={() => update('view', 'map')}
              className={`px-3 py-2 rounded-lg text-sm font-medium ${view === 'map' ? 'bg-pink-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              {t.map}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <p className="text-sm text-gray-500 mb-4">
          {loading ? '...' : `${total} ${t.results}`}
          {city && <span className="ml-1 font-medium text-gray-700">— {city}</span>}
          {category && <span className="ml-1 font-medium text-gray-700">— {categories.find(c => c.slug === category)?.name || category}</span>}
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
    <Suspense fallback={<div className="min-h-screen bg-gray-50 flex items-center justify-center"><div className="text-gray-400">...</div></div>}>
      <SearchContent locale={locale} />
    </Suspense>
  );
}
