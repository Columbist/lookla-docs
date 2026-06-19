'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { SalonDetail } from '@/lib/api';
import ReportButton from '@/components/ReportButton';
import SalonHours from '@/components/SalonHours';

const T: Record<string, Record<string, string>> = {
  el: { call: 'Κλήση', viber: 'Viber', whatsapp: 'WhatsApp', website: 'Ιστοσελίδα', book: 'Κράτηση', message: 'Μήνυμα', request: 'Ζητήστε ραντεβού', report: 'Αναφορά', hours: 'Ώρες λειτουργίας', services: 'Υπηρεσίες', photos: 'Φωτογραφίες', translated: 'Μεταφράστηκε από τα', original: 'Εμφάνιση πρωτοτύπου', verified: 'Επαληθευμένο', not_found: 'Το σαλόνι δεν βρέθηκε', back: 'Πίσω στην αναζήτηση' },
  en: { call: 'Call', viber: 'Viber', whatsapp: 'WhatsApp', website: 'Website', book: 'Book', message: 'Message', request: 'Request slot', report: 'Report', hours: 'Opening hours', services: 'Services', photos: 'Photos', translated: 'Translated from', original: 'Show original', verified: 'Verified', not_found: 'Salon not found', back: 'Back to search' },
  ru: { call: 'Позвонить', viber: 'Viber', whatsapp: 'WhatsApp', website: 'Сайт', book: 'Записаться', message: 'Написать', request: 'Запросить время', report: 'Пожаловаться', hours: 'Часы работы', services: 'Услуги', photos: 'Фото', translated: 'Переведено с', original: 'Показать оригинал', verified: 'Подтверждено', not_found: 'Салон не найден', back: 'Назад к поиску' },
  uk: { call: 'Зателефонувати', viber: 'Viber', whatsapp: 'WhatsApp', website: 'Сайт', book: 'Записатися', message: 'Написати', request: 'Запросити час', report: 'Поскаржитися', hours: 'Години роботи', services: 'Послуги', photos: 'Фото', translated: 'Перекладено з', original: 'Показати оригінал', verified: 'Підтверджено', not_found: 'Салон не знайдено', back: 'Назад до пошуку' },
};

const SOCIAL_ICONS: Record<string, string> = { instagram: '📷', facebook: '👥', facebook_messenger: '💬', viber: '📲', whatsapp: '💬', tiktok: '🎵', youtube: '▶️' };
const SOCIAL_LABELS: Record<string, string> = { instagram: 'Instagram', facebook: 'Facebook', facebook_messenger: 'Messenger', viber: 'Viber', whatsapp: 'WhatsApp', tiktok: 'TikTok', youtube: 'YouTube' };

interface Props { salon: SalonDetail | null; locale: string; slug: string; }

export default function SalonDetailClient({ salon, locale, slug }: Props) {
  const t = T[locale] || T.el;
  const prefix = locale === 'el' ? '' : `/${locale}`;

  if (!salon) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-5xl mb-4">💈</p>
          <h1 className="text-xl font-bold text-gray-800 mb-2">{t.not_found}</h1>
          <Link href={`${prefix}/search`} className="text-pink-600 hover:underline text-sm">{t.back}</Link>
        </div>
      </div>
    );
  }

  const phone = salon.phone_primary?.replace(/\s/g, '');
  const viberLink = salon.social_links?.find(s => s.platform === 'viber')?.url || (phone ? `viber://chat?number=+30${phone}` : null);
  const waLink = salon.social_links?.find(s => s.platform === 'whatsapp')?.url || (phone ? `https://wa.me/30${phone}` : null);

  // Pick best description for locale
  const descMap: Record<string, string | undefined> = { el: salon.description_el || salon.description, en: salon.description, ru: salon.description_ru || salon.description, uk: salon.description_uk || salon.description };
  const desc = descMap[locale] || salon.description;
  const isTranslated = desc && desc !== (salon.description_el || salon.description) && locale !== 'el';

  // Schema.org
  const schema = {
    '@context': 'https://schema.org', '@type': 'BeautySalon',
    name: salon.name,
    address: { '@type': 'PostalAddress', streetAddress: salon.address_street, addressLocality: salon.address_city, addressCountry: 'GR' },
    telephone: salon.phone_primary, url: salon.website,
    ...(salon.rating_google ? { aggregateRating: { '@type': 'AggregateRating', ratingValue: salon.rating_google, reviewCount: salon.rating_count } } : {}),
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />

      <header className="bg-white border-b sticky top-0 z-30 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <Link href={`${prefix}/search`} className="text-gray-400 hover:text-gray-600 text-xl">←</Link>
          <Link href={prefix || '/'} className="text-pink-600 font-bold text-lg">Lookla</Link>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Photo gallery */}
        {salon.photos.length > 0 ? (
          <div className={`grid gap-1.5 rounded-xl overflow-hidden mb-6 h-56 ${salon.photos.length >= 3 ? 'grid-cols-3' : salon.photos.length === 2 ? 'grid-cols-2' : 'grid-cols-1'}`}>
            {salon.photos.slice(0, 3).map((photo, i) => (
              <div key={photo.id} className={`relative bg-gray-100 ${i === 0 && salon.photos.length >= 3 ? 'col-span-2' : ''}`}>
                <img src={photo.url} alt={salon.name} className="w-full h-full object-cover" loading={i === 0 ? 'eager' : 'lazy'} />
              </div>
            ))}
          </div>
        ) : (
          <div className="h-48 rounded-xl bg-gradient-to-br from-pink-50 to-purple-50 flex items-center justify-center text-6xl mb-6">💈</div>
        )}

        {/* Title + meta */}
        <div className="bg-white rounded-xl p-5 mb-4">
          <div className="flex items-start justify-between gap-3 mb-4">
            <div>
              <h1 className="text-xl font-bold text-gray-900 mb-1">{salon.name}</h1>
              <p className="text-gray-500 text-sm">
                {[salon.address_street, salon.address_number, salon.address_city].filter(Boolean).join(' ')}
              </p>
              {salon.rating_google && (
                <div className="flex items-center gap-1.5 mt-2">
                  <span className="text-yellow-400 text-sm">★</span>
                  <span className="font-semibold text-sm text-gray-800">{parseFloat(salon.rating_google).toFixed(1)}</span>
                  <span className="text-gray-400 text-xs">({salon.rating_count} αξιολογήσεις)</span>
                </div>
              )}
            </div>
            {salon.is_verified && (
              <span className="shrink-0 bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded-full font-medium">✓ {t.verified}</span>
            )}
          </div>

          {/* CTA buttons */}
          <div className="space-y-2">
            <div className="flex gap-2">
              <button className="flex-1 py-2.5 bg-pink-600 text-white rounded-xl text-sm font-semibold hover:bg-pink-700">📅 {t.book}</button>
              <button className="flex-1 py-2.5 border border-pink-200 text-pink-600 rounded-xl text-sm font-medium hover:bg-pink-50">⏰ {t.request}</button>
            </div>
            <div className="flex flex-wrap gap-2">
              {phone && <a href={`tel:${phone}`} className="flex items-center gap-1.5 px-3 py-2 bg-green-50 text-green-700 rounded-xl text-sm font-medium hover:bg-green-100">📞 {t.call}</a>}
              {viberLink && <a href={viberLink} className="flex items-center gap-1.5 px-3 py-2 bg-purple-50 text-purple-700 rounded-xl text-sm font-medium hover:bg-purple-100">📲 {t.viber}</a>}
              {waLink && <a href={waLink} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 px-3 py-2 bg-emerald-50 text-emerald-700 rounded-xl text-sm font-medium hover:bg-emerald-100">💬 {t.whatsapp}</a>}
              {salon.website && <a href={salon.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 px-3 py-2 bg-blue-50 text-blue-700 rounded-xl text-sm font-medium hover:bg-blue-100">🌐 {t.website}</a>}
              <button className="flex items-center gap-1.5 px-3 py-2 bg-gray-50 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-100">✉️ {t.message}</button>
            </div>
          </div>
        </div>

        {/* Description */}
        {desc && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <p className="text-gray-700 text-sm leading-relaxed">{desc}</p>
            {isTranslated && (
              <p className="text-xs text-gray-400 mt-3 flex items-center gap-1">🌐 {t.translated} Greek</p>
            )}
          </div>
        )}

        {/* Services */}
        {salon.services.length > 0 && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <h2 className="font-semibold text-gray-800 mb-3">{t.services}</h2>
            <div className="divide-y divide-gray-50">
              {salon.services.slice(0, 15).map(svc => (
                <div key={svc.id} className="py-2.5 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-800">{svc.name_el || svc.name}</p>
                    {svc.duration_min && <p className="text-xs text-gray-400">{svc.duration_min} λεπτά</p>}
                  </div>
                  {svc.price_from && (
                    <span className="text-sm font-medium text-gray-700 ml-4 shrink-0">
                      {svc.price_to && String(svc.price_to) !== String(svc.price_from) ? `${svc.price_from}–${svc.price_to}€` : `${svc.price_from}€`}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Hours */}
        {salon.hours.length > 0 && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <h2 className="font-semibold text-gray-800 mb-3">{t.hours}</h2>
            <SalonHours hours={salon.hours} locale={locale} />
          </div>
        )}

        {/* Social links */}
        {salon.social_links.length > 0 && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <div className="flex flex-wrap gap-3">
              {salon.social_links.map(sl => (
                <a key={sl.platform} href={sl.url} target="_blank" rel="noopener noreferrer"
                   className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-pink-600 border border-gray-100 px-3 py-1.5 rounded-full hover:border-pink-200 transition-colors">
                  <span>{SOCIAL_ICONS[sl.platform] || '🔗'}</span>
                  <span>{SOCIAL_LABELS[sl.platform] || sl.platform}</span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Map placeholder */}
        {salon.lat && salon.lng && (
          <div className="bg-white rounded-xl p-4 mb-4">
            <p className="text-sm text-gray-500">📍 {[salon.address_street, salon.address_number, salon.address_city].filter(Boolean).join(', ')}</p>
            <a href={`https://www.google.com/maps/search/?api=1&query=${salon.lat},${salon.lng}`}
               target="_blank" rel="noopener noreferrer"
               className="text-xs text-blue-600 hover:underline mt-1 block">Άνοιγμα στο Google Maps →</a>
          </div>
        )}

        {/* Report */}
        <div className="text-center mt-6 mb-8">
          <ReportButton salonId={salon.id} locale={locale} label={t.report} />
        </div>
      </div>
    </div>
  );
}
