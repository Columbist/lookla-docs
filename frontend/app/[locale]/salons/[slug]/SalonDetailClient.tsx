'use client';
import Link from 'next/link';
import { useState, useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import type { SalonDetail, ServiceItem, ReviewItem } from '@/lib/api';
import ReportButton from '@/components/ReportButton';
import SalonHours from '@/components/SalonHours';

const SOCIAL_ICONS: Record<string, string> = { instagram: '📷', facebook: '👥', facebook_messenger: '💬', viber: '📲', whatsapp: '💬', tiktok: '🎵', youtube: '▶️' };
const SOCIAL_LABELS: Record<string, string> = { instagram: 'Instagram', facebook: 'Facebook', facebook_messenger: 'Messenger', viber: 'Viber', whatsapp: 'WhatsApp', tiktok: 'TikTok', youtube: 'YouTube' };

interface Props { salon: SalonDetail | null; locale: string; slug: string; }

const TRANSLATED_LABEL: Record<string, string> = {
  el: 'Μεταφράστηκε', en: 'Translated', ru: 'Переведено', uk: 'Перекладено',
};

function TranslatedBadge({ locale }: { locale: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs text-gray-400 ml-1.5">
      🌐 {TRANSLATED_LABEL[locale] ?? 'Translated'}
    </span>
  );
}

function useLazySection<T>(
  salonId: number,
  path: 'services' | 'reviews',
  locale: string,
): [T[], boolean, React.RefObject<HTMLDivElement>] {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const fetched = useRef(false);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting || fetched.current) return;
      fetched.current = true;
      obs.disconnect();
      fetch(`/api/salons/${salonId}/${path}?lang=${locale}`)
        .then(r => r.json())
        .then((d: T[]) => { setData(Array.isArray(d) ? d : []); setLoading(false); })
        .catch(() => setLoading(false));
    }, { rootMargin: '400px' });
    obs.observe(el);
    return () => obs.disconnect();
  }, [salonId, path, locale]);

  return [data, loading, sentinelRef];
}

export default function SalonDetailClient({ salon, locale, slug }: Props) {
  const t = useTranslations('salon');
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const [showAllPhotos, setShowAllPhotos] = useState(false);

  const [services, servicesLoading, servicesRef] = useLazySection<ServiceItem>(salon?.id ?? 0, 'services', locale);
  const [reviews, reviewsLoading, reviewsRef] = useLazySection<ReviewItem>(salon?.id ?? 0, 'reviews', locale);

  if (!salon) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-5xl mb-4">💈</p>
          <h1 className="text-xl font-bold text-gray-800 mb-2">{t('not_found')}</h1>
          <Link href={`${prefix}/search`} className="text-pink-600 hover:underline text-sm">{t('back')}</Link>
        </div>
      </div>
    );
  }

  const phone = salon.phone_primary?.replace(/\s/g, '');
  const e164 = phone ? (phone.startsWith('+') ? phone.replace(/\D/g, '') : `30${phone.replace(/\D/g, '')}`) : null;
  const viberLink = salon.social_links?.find(s => s.platform === 'viber')?.url || (e164 ? `viber://chat?number=+${e164}` : null);
  const waLink = salon.social_links?.find(s => s.platform === 'whatsapp')?.url || (e164 ? `https://wa.me/${e164}` : null);

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
          <div className="mb-6">
            <div className={`grid gap-1.5 rounded-xl overflow-hidden h-56 ${salon.photos.length >= 3 ? 'grid-cols-3' : salon.photos.length === 2 ? 'grid-cols-2' : 'grid-cols-1'}`}>
              {salon.photos.slice(0, 3).map((photo, i) => (
                <div key={photo.id} className={`relative bg-gray-100 ${i === 0 && salon.photos.length >= 3 ? 'col-span-2' : ''}`}>
                  <img src={photo.url} alt={salon.name} className="w-full h-full object-cover" loading={i === 0 ? 'eager' : 'lazy'} />
                  {i === 2 && salon.photos.length > 3 && !showAllPhotos && (
                    <button onClick={() => setShowAllPhotos(true)}
                      className="absolute inset-0 bg-black/50 text-white flex items-center justify-center text-sm font-semibold hover:bg-black/60 transition-colors">
                      +{salon.photos.length - 3} φωτογραφίες
                    </button>
                  )}
                </div>
              ))}
            </div>
            {showAllPhotos && salon.photos.length > 3 && (
              <div className="grid grid-cols-3 gap-1.5 mt-1.5">
                {salon.photos.slice(3).map((photo) => (
                  <div key={photo.id} className="relative bg-gray-100 h-32 rounded-lg overflow-hidden">
                    <img src={photo.url} alt={salon.name} className="w-full h-full object-cover" loading="lazy" />
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="h-48 rounded-xl bg-gradient-to-br from-pink-50 to-purple-50 flex items-center justify-center text-6xl mb-6">💈</div>
        )}

        {/* Title + meta */}
        <div className="bg-white rounded-xl p-5 mb-4">
          <div className="flex items-start justify-between gap-3 mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-1">{salon.name}</h1>
              <p className="text-gray-500 text-base">
                {[salon.address_street, salon.address_number, salon.address_city].filter(Boolean).join(' ')}
              </p>
              {salon.rating_google && (
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-yellow-400">★</span>
                  <span className="font-bold text-base text-gray-800">{parseFloat(salon.rating_google).toFixed(1)}</span>
                  <span className="text-gray-400 text-sm">({t('reviews_count', { count: salon.rating_count })})</span>
                </div>
              )}
            </div>
            {salon.is_verified && (
              <span className="shrink-0 bg-blue-50 text-blue-600 text-sm px-3 py-1.5 rounded-full font-medium">✓ {t('verified')}</span>
            )}
          </div>

          {/* Address detail */}
          {(salon.address_region || salon.address_postal) && (
            <p className="text-sm text-gray-400 mt-1">
              {[salon.address_postal, salon.address_region].filter(Boolean).join(' · ')}
            </p>
          )}

          {/* CTA buttons */}
          <div className="space-y-3">
            <div className="flex gap-2">
              <button className="flex-1 py-4 bg-pink-600 text-white rounded-xl text-base font-bold hover:bg-pink-700">📅 {t('book')}</button>
              <button className="flex-1 py-4 border border-pink-200 text-pink-600 rounded-xl text-base font-semibold hover:bg-pink-50">⏰ {t('request')}</button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {phone && <a href={`tel:${phone}`} className="flex items-center justify-center gap-2 px-4 py-3.5 bg-green-50 text-green-700 rounded-xl text-base font-semibold hover:bg-green-100">📞 {t('call')}</a>}
              {viberLink && <a href={viberLink} className="flex items-center justify-center gap-2 px-4 py-3.5 bg-purple-50 text-purple-700 rounded-xl text-base font-semibold hover:bg-purple-100">📲 {t('viber')}</a>}
              {waLink && <a href={waLink} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2 px-4 py-3.5 bg-emerald-50 text-emerald-700 rounded-xl text-base font-semibold hover:bg-emerald-100">💬 {t('whatsapp')}</a>}
              {salon.website && <a href={salon.website} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2 px-4 py-3.5 bg-blue-50 text-blue-700 rounded-xl text-base font-semibold hover:bg-blue-100">🌐 {t('website')}</a>}
              <button className="flex items-center justify-center gap-2 px-4 py-3.5 bg-gray-50 text-gray-600 rounded-xl text-base font-semibold hover:bg-gray-100">✉️ {t('message')}</button>
            </div>
          </div>
        </div>

        {/* Description */}
        {desc && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <p className="text-gray-700 text-base leading-relaxed">{desc}</p>
            {isTranslated && (
              <p className="text-xs text-gray-400 mt-3 flex items-center gap-1">🌐 {t('translated')} Greek</p>
            )}
          </div>
        )}

        {/* Services — lazy-loaded */}
        <div ref={servicesRef}>
          {servicesLoading ? (
            <div className="bg-white rounded-xl p-5 mb-4 space-y-3">
              {[1,2,3].map(i => <div key={i} className="h-10 bg-gray-100 rounded animate-pulse" />)}
            </div>
          ) : services.length > 0 && (
            <div className="bg-white rounded-xl p-5 mb-4">
              <h2 className="text-lg font-bold text-gray-800 mb-3">{t('services')}</h2>
              <div className="divide-y divide-gray-100">
                {services.map(svc => (
                  <div key={svc.id} className="py-3.5 flex items-center justify-between">
                    <div>
                      <p className="text-base text-gray-800">
                        {svc.name}
                        {svc.is_translated && <TranslatedBadge locale={locale} />}
                      </p>
                      {svc.duration_min && <p className="text-sm text-gray-400 mt-0.5">{svc.duration_min} {t('minutes')}</p>}
                    </div>
                    {svc.price_from && (
                      <span className="text-base font-semibold text-gray-700 ml-4 shrink-0">
                        {svc.price_to && String(svc.price_to) !== String(svc.price_from) ? `${svc.price_from}–${svc.price_to}€` : `${svc.price_from}€`}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Reviews — lazy-loaded */}
        <div ref={reviewsRef}>
          {reviewsLoading ? (
            <div className="bg-white rounded-xl p-5 mb-4 space-y-4">
              {[1,2,3].map(i => (
                <div key={i} className="space-y-2">
                  <div className="h-3 w-32 bg-gray-100 rounded animate-pulse" />
                  <div className="h-12 bg-gray-100 rounded animate-pulse" />
                </div>
              ))}
            </div>
          ) : reviews.length > 0 && (
            <div className="bg-white rounded-xl p-5 mb-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-bold text-gray-800">{t('reviews')}</h2>
                {salon.review_count > reviews.length && (
                  <span className="text-sm text-gray-400">{t('reviews_count', { count: salon.review_count })}</span>
                )}
              </div>
              <div className="space-y-4">
                {reviews.map(rev => (
                  <div key={rev.id} className="border-b border-gray-50 last:border-0 pb-4 last:pb-0">
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-gray-800">{rev.author_name || t('anonymous')}</span>
                        {rev.source !== 'google' && (
                          <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full capitalize">{rev.source}</span>
                        )}
                        {rev.is_translated && <TranslatedBadge locale={locale} />}
                      </div>
                      <div className="flex items-center gap-1.5">
                        {rev.rating && <span className="text-yellow-400 text-sm">{'★'.repeat(rev.rating)}{'☆'.repeat(5 - rev.rating)}</span>}
                        {rev.published_at && <span className="text-xs text-gray-400">{rev.published_at.slice(0, 7)}</span>}
                      </div>
                    </div>
                    {rev.text && <p className="text-sm text-gray-600 leading-relaxed">{rev.text}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Hours */}
        {salon.hours.length > 0 && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <h2 className="text-lg font-bold text-gray-800 mb-3">{t('hours')}</h2>
            <SalonHours hours={salon.hours} locale={locale} />
          </div>
        )}

        {/* Social links */}
        {salon.social_links.length > 0 && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <div className="flex flex-wrap gap-3">
              {salon.social_links.map(sl => (
                <a key={sl.platform} href={sl.url} target="_blank" rel="noopener noreferrer"
                   className="flex items-center gap-2 text-base text-gray-600 hover:text-pink-600 border border-gray-100 px-4 py-2.5 rounded-full hover:border-pink-200 transition-colors">
                  <span>{SOCIAL_ICONS[sl.platform] || '🔗'}</span>
                  <span>{SOCIAL_LABELS[sl.platform] || sl.platform}</span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Map placeholder */}
        {salon.lat && salon.lng && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <p className="text-base text-gray-500">📍 {[salon.address_street, salon.address_number, salon.address_city, salon.address_postal].filter(Boolean).join(', ')}</p>
            {salon.address_region && <p className="text-sm text-gray-400 mt-0.5">{salon.address_region}</p>}
            <a href={`https://www.google.com/maps/search/?api=1&query=${salon.lat},${salon.lng}`}
               target="_blank" rel="noopener noreferrer"
               className="text-base text-blue-600 hover:underline mt-1.5 block">{t('open_maps')}</a>
          </div>
        )}

        {/* Data freshness */}
        {salon.data_verified_at && (
          <p className="text-center text-xs text-gray-300 mb-4">
            {t('data_updated')} {new Date(salon.data_verified_at).toLocaleDateString(locale === 'el' ? 'el-GR' : locale, { year: 'numeric', month: 'long' })}
          </p>
        )}

        {/* Report */}
        <div className="text-center mt-6 mb-8">
          <ReportButton salonId={salon.id} locale={locale} label={t('report')} />
        </div>
      </div>
    </div>
  );
}
