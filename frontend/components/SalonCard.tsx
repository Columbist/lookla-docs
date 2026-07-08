import Link from 'next/link';
import type { SalonListItem } from '@/lib/api';

const STARS = (r?: string) => {
  const n = parseFloat(r || '0');
  const full = Math.floor(n);
  const half = n - full >= 0.5 ? 1 : 0;
  return '★'.repeat(full) + (half ? '✩' : '') + '☆'.repeat(5 - full - half);
};

// Gender audience per category slug — used to show who the price applies to
const CATEGORY_GENDER: Record<string, string> = {
  barbershop:      '♂',
  hair:            '♀ ♂',
  hair_cut:        '♀ ♂',
  hair_color:      '♀',
  hair_highlights: '♀',
  hair_treatment:  '♀ ♂',
  hair_styling:    '♀',
  hair_extensions: '♀',
  nails:           '♀',
  nail_art:        '♀',
  manicure:        '♀',
  pedicure:        '♀',
  gel_nails:       '♀',
  acrylic_nails:   '♀',
  skin:            '♀',
  waxing:          '♀',
  lashes_brows:    '♀',
  makeup:          '♀',
  massage:         '♀ ♂',
  spa:             '♀ ♂',
  tattoo_piercing: '♀ ♂',
};

const OPEN_LABEL: Record<string, [string, string]> = {
  el: ['Ανοιχτό', 'Κλειστό'],
  en: ['Open', 'Closed'],
  ru: ['Открыто', 'Закрыто'],
  uk: ['Відкрито', 'Зачинено'],
};

const FROM_LABEL: Record<string, string> = {
  el: 'από', en: 'from', ru: 'от', uk: 'від',
};

interface Props {
  salon: SalonListItem;
  locale: string;
  category?: string;
}

export default function SalonCard({ salon, locale, category }: Props) {
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const href = `${prefix}/salons/${salon.slug || salon.id}`;
  const [openLabel, closedLabel] = OPEN_LABEL[locale] ?? OPEN_LABEL.en;
  const fromLabel = FROM_LABEL[locale] ?? 'από';
  const genderIcon = category ? CATEGORY_GENDER[category] : undefined;

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
        {/* Open/Closed badge on photo */}
        {salon.is_open_now !== undefined && salon.is_open_now !== null && (
          <span className={`absolute bottom-2 left-2 text-xs px-2 py-0.5 rounded-full font-medium shadow-sm ${salon.is_open_now ? 'bg-green-500 text-white' : 'bg-black/50 text-gray-200'}`}>
            {salon.is_open_now ? openLabel : closedLabel}
          </span>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <h3 className="font-semibold text-gray-900 text-sm leading-tight mb-1 line-clamp-1">{salon.name}</h3>
        <p className="text-xs text-gray-500 mb-2 line-clamp-1">
          {[salon.address_street, salon.address_number].filter(Boolean).join(' ')}{salon.address_city ? `, ${salon.address_city}` : ''}
        </p>

        <div className="flex items-center justify-between gap-2">
          {/* Rating */}
          <div className="flex items-center gap-1 min-w-0">
            {salon.rating_google ? (
              <>
                <span className="text-yellow-400 text-xs">{STARS(salon.rating_google)}</span>
                <span className="text-xs text-gray-600 font-medium">{parseFloat(salon.rating_google).toFixed(1)}</span>
                <span className="text-xs text-gray-400">({salon.rating_count})</span>
              </>
            ) : (
              <span className="text-xs text-gray-300">—</span>
            )}
          </div>

          {/* Min price */}
          {salon.min_price != null && salon.min_price > 0 && (
            <div className="flex items-center gap-1 shrink-0">
              <span className="text-xs text-gray-400">{fromLabel}</span>
              <span className="text-sm font-semibold text-gray-700">{Math.round(salon.min_price)}€</span>
              {genderIcon && (
                <span className="text-xs text-gray-400">{genderIcon}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
