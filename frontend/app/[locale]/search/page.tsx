'use client';
import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import type { SalonListItem, City, Category } from '@/lib/api';
import SalonCard from '@/components/SalonCard';
import dynamic from 'next/dynamic';

const MapView = dynamic(() => import('@/components/MapView'), { ssr: false });

const LIMIT = 24;

function SearchContent({ locale }: { locale: string }) {
  const sp = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations('search');
  const inputRef = useRef<HTMLInputElement>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const city = sp.get('city') || '';
  const category = sp.get('category') || '';
  const q = sp.get('q') || '';
  const view = sp.get('view') || 'list';
  const minRating = sp.get('min_rating') || '';

  const [salons, setSalons] = useState<SalonListItem[]>([]);
  const [mapSalons, setMapSalons] = useState<SalonListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [cities, setCities] = useState<City[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [mapLoading, setMapLoading] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const filtersRef = useRef<HTMLDivElement>(null);

  // Refs for use inside IntersectionObserver callback (avoids stale closures)
  const pageRef = useRef(1);
  const hasMoreRef = useRef(false);
  const busyRef = useRef(false);

  useEffect(() => {
    fetch(`/api/cities`).then(r => r.json()).then(setCities).catch(() => {});
    fetch(`/api/categories?lang=${locale}`).then(r => r.json()).then(setCategories).catch(() => {});
  }, [locale]);

  useEffect(() => {
    if (!filtersOpen) return;
    const handler = (e: MouseEvent) => {
      if (filtersRef.current && !filtersRef.current.contains(e.target as Node)) {
        setFiltersOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [filtersOpen]);

  const buildParams = useCallback((page: number) => {
    const params = new URLSearchParams({ limit: String(LIMIT), page: String(page) });
    if (city) params.set('city', city);
    if (q) params.set('q', q);
    if (category) params.set('category', category);
    if (minRating) params.set('min_rating', minRating);
    return params;
  }, [city, q, category, minRating]);

  const loadMore = useCallback(async () => {
    if (busyRef.current || !hasMoreRef.current) return;
    busyRef.current = true;
    const nextPage = pageRef.current + 1;
    setLoadingMore(true);
    try {
      const d = await fetch(`/api/salons?${buildParams(nextPage)}`).then(r => r.json());
      setSalons(prev => [...prev, ...(d.items || [])]);
      pageRef.current = nextPage;
      hasMoreRef.current = nextPage < (d.pages || 1);
    } catch {}
    setLoadingMore(false);
    busyRef.current = false;
  }, [buildParams]);

  // Reset + initial fetch when filters change
  useEffect(() => {
    pageRef.current = 1;
    hasMoreRef.current = false;
    busyRef.current = false;
    setLoading(true);
    setSalons([]);
    fetch(`/api/salons?${buildParams(1)}`)
      .then(r => r.json())
      .then(d => {
        setSalons(d.items || []);
        setTotal(d.total || 0);
        pageRef.current = 1;
        hasMoreRef.current = 1 < (d.pages || 1);
      })
      .catch(() => { setSalons([]); setTotal(0); hasMoreRef.current = false; })
      .finally(() => setLoading(false));
  }, [city, q, category, minRating]); // eslint-disable-line react-hooks/exhaustive-deps

  // Map fetch
  useEffect(() => {
    if (view !== 'map') return;
    setMapLoading(true);
    const params = new URLSearchParams();
    if (city) params.set('city', city);
    if (q) params.set('q', q);
    if (category) params.set('category', category);
    if (minRating) params.set('min_rating', minRating);
    fetch(`/api/salons/map?${params}`)
      .then(r => r.json())
      .then(d => setMapSalons(Array.isArray(d) ? d : []))
      .catch(() => setMapSalons([]))
      .finally(() => setMapLoading(false));
  }, [view, city, q, category, minRating]);

  // IntersectionObserver — fires loadMore when sentinel enters viewport
  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => { if (entries[0].isIntersecting) loadMore(); },
      { rootMargin: '300px' }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [loadMore]);

  const update = useCallback((key: string, value: string) => {
    const p = new URLSearchParams(sp.toString());
    if (value) p.set(key, value); else p.delete(key);
    if (key !== 'view') p.delete('page');
    router.push(`${pathname}?${p}`);
  }, [sp, router, pathname]);

  const doSearch = () => update('q', inputRef.current?.value || '');
  const prefix = locale === 'el' ? '' : `/${locale}`;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-100 px-4 py-3 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center gap-2">
          <Link href={prefix || '/'} className="text-xl font-bold text-pink-600 shrink-0 mr-1">Lookla</Link>

          <div className="flex items-center border border-gray-200 rounded-lg overflow-hidden flex-1 min-w-[160px] max-w-xs">
            <input
              ref={inputRef}
              type="text"
              defaultValue={q}
              placeholder={t('placeholder')}
              onKeyDown={e => e.key === 'Enter' && doSearch()}
              className="px-3 py-2 text-sm focus:outline-none flex-1 min-w-0"
            />
            <button onClick={doSearch} className="px-3 py-2 bg-pink-600 text-white text-sm font-medium hover:bg-pink-700 shrink-0">
              🔍
            </button>
          </div>

          {/* Filter button */}
          <div className="relative" ref={filtersRef}>
            {(() => {
              const activeCount = [city, category, minRating].filter(Boolean).length;
              return (
                <button
                  onClick={() => setFiltersOpen(o => !o)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-sm font-medium transition-colors ${filtersOpen || activeCount > 0 ? 'bg-pink-600 text-white border-pink-600' : 'border-gray-200 text-gray-700 hover:bg-gray-50'}`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                    <path fillRule="evenodd" d="M2.628 1.601C5.028 1.206 7.49 1 10 1s4.973.206 7.372.601a.75.75 0 01.628.74v2.288a2.25 2.25 0 01-.659 1.59l-4.682 4.683a2.25 2.25 0 00-.659 1.59v3.037c0 .684-.31 1.33-.844 1.757l-1.937 1.55A.75.75 0 018 18.25v-5.757a2.25 2.25 0 00-.659-1.591L2.659 6.22A2.25 2.25 0 012 4.629V2.34a.75.75 0 01.628-.74z" clipRule="evenodd" />
                  </svg>
                  {activeCount > 0 && (
                    <span className={`text-xs font-bold w-4 h-4 rounded-full flex items-center justify-center ${filtersOpen || activeCount > 0 ? 'bg-white text-pink-600' : 'bg-pink-600 text-white'}`}>
                      {activeCount}
                    </span>
                  )}
                </button>
              );
            })()}

            {filtersOpen && (
              <div className="absolute top-full right-0 mt-2 w-72 max-w-[calc(100vw-1rem)] bg-white rounded-xl shadow-lg border border-gray-100 p-4 z-50 space-y-3">
                <div>
                  <label className="text-xs font-medium text-gray-500 mb-1 block">{t('filter_city')}</label>
                  <select value={city} onChange={e => { update('city', e.target.value); }}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-pink-200">
                    <option value="">{t('all_cities')}</option>
                    {cities.slice(0, 30).map(c => <option key={c.city} value={c.city}>{c.city} ({c.count})</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 mb-1 block">{t('filter_category')}</label>
                  <select value={category} onChange={e => { update('category', e.target.value); }}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-pink-200">
                    <option value="">{t('all_cats')}</option>
                    {categories.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 mb-1 block">{t('filter_rating')}</label>
                  <select value={minRating} onChange={e => { update('min_rating', e.target.value); }}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-pink-200">
                    <option value="">Όλες οι αξιολογήσεις</option>
                    <option value="3">★ 3+</option>
                    <option value="4">★ 4+</option>
                    <option value="4.5">★ 4.5+</option>
                  </select>
                </div>
                {(city || category || minRating) && (
                  <button onClick={() => { ['city','category','min_rating'].forEach(k => update(k, '')); setFiltersOpen(false); }}
                    className="w-full text-xs text-gray-400 hover:text-red-500 pt-1">
                    ✕ Εκκαθάριση φίλτρων
                  </button>
                )}
              </div>
            )}
          </div>

          <div className="ml-auto flex items-center gap-1 shrink-0">
            <button onClick={() => update('view', 'list')}
              className={`px-3 py-2 rounded-lg text-sm font-medium ${view !== 'map' ? 'bg-pink-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              {t('list')}
            </button>
            <button onClick={() => update('view', 'map')}
              className={`px-3 py-2 rounded-lg text-sm font-medium ${view === 'map' ? 'bg-pink-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              {t('map')}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <p className="text-sm text-gray-500 mb-4">
          {loading ? '...' : `${total} ${t('results')}`}
          {city && <span className="ml-1 font-medium text-gray-700">— {city}</span>}
          {category && <span className="ml-1 font-medium text-gray-700">— {categories.find(c => c.slug === category)?.name || category}</span>}
        </p>

        {view === 'map' ? (
          mapLoading
            ? <div className="flex items-center justify-center h-96 text-gray-400">...</div>
            : <MapView salons={mapSalons} locale={locale} />
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {loading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="bg-white rounded-xl h-64 animate-pulse border border-gray-100" />
                ))
              ) : salons.length > 0 ? (
                salons.map(salon => <SalonCard key={salon.id} salon={salon} locale={locale} />)
              ) : (
                <div className="col-span-3 text-center py-16 text-gray-400">{t('no_results')}</div>
              )}
            </div>

            {/* Sentinel + spinner */}
            <div ref={sentinelRef} className="h-16 flex items-center justify-center mt-4">
              {loadingMore && (
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              )}
            </div>
          </>
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
