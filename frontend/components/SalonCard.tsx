import Link from 'next/link';
import type { SalonListItem } from '@/lib/api';

const STARS = (r?: string) => {
  const n = parseFloat(r || '0');
  return '★'.repeat(Math.round(n)) + '☆'.repeat(5 - Math.round(n));
};

const PRICE = (level?: number) => ['', '€', '€€', '€€€'][level || 0] || '';

export default function SalonCard({ salon, locale }: { salon: SalonListItem; locale: string }) {
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const href = `${prefix}/salons/${salon.slug || salon.id}`;

  return (
    <Link href={href} className="bg-white rounded-xl border border-gray-100 overflow-hidden hover:shadow-md hover:border-pink-100 transition-all group">
      {/* Photo */}
      <div className="relative h-44 bg-gradient-to-br from-pink-50 to-purple-50">
        {salon.primary_photo ? (
          <img
            src={salon.primary_photo}
            alt={salon.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
            onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-5xl">💈</div>
        )}
        {salon.is_verified && (
          <span className="absolute top-2 right-2 bg-white text-xs text-blue-600 px-2 py-0.5 rounded-full shadow-sm font-medium">✓</span>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <h3 className="font-semibold text-gray-900 text-sm leading-tight mb-1 line-clamp-1">{salon.name}</h3>
        <p className="text-xs text-gray-500 mb-2 line-clamp-1">
          {[salon.address_street, salon.address_number].filter(Boolean).join(' ')}{salon.address_city ? `, ${salon.address_city}` : ''}
        </p>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            {salon.rating_google && (
              <>
                <span className="text-yellow-400 text-xs">{STARS(salon.rating_google)}</span>
                <span className="text-xs text-gray-500">{parseFloat(salon.rating_google).toFixed(1)}</span>
                <span className="text-xs text-gray-400">({salon.rating_count})</span>
              </>
            )}
          </div>
          {salon.price_level && (
            <span className="text-xs text-gray-500 font-medium">{PRICE(salon.price_level)}</span>
          )}
        </div>
      </div>
    </Link>
  );
}
