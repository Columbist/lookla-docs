import Link from 'next/link';
import type { City } from '@/lib/api';

const SALONS_WORD: Record<string, string> = {
  el: 'σαλόνια', en: 'salons', ru: 'салонов', uk: 'салонів',
};

export default function CityGrid({ cities, locale }: { cities: City[]; locale: string }) {
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const word = SALONS_WORD[locale] || 'salons';
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
      {cities.map(city => (
        <Link
          key={city.city}
          href={`${prefix}/search?city=${encodeURIComponent(city.city)}`}
          className="p-3 bg-white rounded-xl border border-gray-100 hover:border-pink-200 hover:shadow-sm transition-all"
        >
          <div className="text-sm font-medium text-gray-800 truncate">{city.city}</div>
          <div className="text-xs text-gray-400 mt-0.5">{city.count} {word}</div>
        </Link>
      ))}
    </div>
  );
}
