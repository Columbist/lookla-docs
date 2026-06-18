import { getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { Metadata } from 'next';
import ContactButtons from '@/components/ContactButtons';
import SalonHours from '@/components/SalonHours';
import ReportButton from '@/components/ReportButton';

interface Props {
  params: { locale: string; slug: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const salon = await api.salons.get(slug).catch(() => null);
  if (!salon) return { title: 'Not found' };
  return {
    title: salon.name,
    description: salon.description?.slice(0, 160) || `${salon.name} — ${salon.address_city}`,
    openGraph: { images: salon.primary_photo ? [salon.primary_photo] : [] },
  };
}

export default async function SalonPage({ params }: Props) {
  const { locale, slug } = await params;
  const t = await getTranslations('salon');
  const salon = await api.salons.get(slug).catch(() => null);
  if (!salon) notFound();

  const prefix = locale === 'el' ? '' : `/${locale}`;

  // Pick description in user's language
  const descMap: Record<string, string | undefined> = {
    el: salon.description_el || salon.description,
    en: salon.description,
    ru: salon.description_ru || salon.description,
    uk: salon.description_uk || salon.description,
  };
  const desc = descMap[locale] || salon.description;
  const isTranslated = desc && desc !== (salon.description_el || salon.description);

  // Schema.org LocalBusiness
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'BeautySalon',
    name: salon.name,
    address: { '@type': 'PostalAddress', streetAddress: salon.address_street, addressLocality: salon.address_city, addressCountry: 'GR' },
    telephone: salon.phone_primary,
    url: salon.website,
    aggregateRating: salon.rating_google ? { '@type': 'AggregateRating', ratingValue: salon.rating_google, reviewCount: salon.rating_count } : undefined,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />

      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-30 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <Link href={`${prefix}/search`} className="text-gray-400 hover:text-gray-600 text-lg">←</Link>
          <Link href={`${prefix}`} className="text-pink-600 font-bold text-lg">Lookla</Link>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Photo gallery */}
        <div className="grid grid-cols-3 gap-1.5 rounded-xl overflow-hidden mb-6 h-56">
          {salon.photos.slice(0, 3).map((photo, i) => (
            <div key={photo.id} className={`relative bg-gray-100 ${i === 0 ? 'col-span-2 row-span-2' : ''}`}>
              <img src={photo.url} alt={salon.name} className="w-full h-full object-cover" loading="lazy"
                onError={e => { (e.target as HTMLImageElement).parentElement!.style.background = '#f3f4f6'; }} />
            </div>
          ))}
          {salon.photos.length === 0 && (
            <div className="col-span-3 flex items-center justify-center bg-gradient-to-br from-pink-50 to-purple-50 text-6xl">💈</div>
          )}
        </div>

        {/* Title + meta */}
        <div className="bg-white rounded-xl p-5 mb-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h1 className="text-xl font-bold text-gray-900 mb-1">{salon.name}</h1>
              <p className="text-gray-500 text-sm">
                {[salon.address_street, salon.address_number, salon.address_city].filter(Boolean).join(' ')}
              </p>
              {salon.rating_google && (
                <div className="flex items-center gap-1 mt-2">
                  <span className="text-yellow-400">★</span>
                  <span className="font-medium text-sm">{parseFloat(salon.rating_google).toFixed(1)}</span>
                  <span className="text-gray-400 text-xs">({salon.rating_count} αξιολογήσεις)</span>
                </div>
              )}
            </div>
            {salon.is_verified && (
              <span className="flex-shrink-0 bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded-full font-medium">✓ {t('verified')}</span>
            )}
          </div>

          {/* Contact buttons */}
          <div className="mt-4">
            <ContactButtons salon={salon} t_call={t('call')} t_viber={t('viber')} t_whatsapp={t('whatsapp')} t_website={t('website')} t_message={t('message')} t_book={t('book')} t_request={t('request_slot')} locale={locale} />
          </div>
        </div>

        {/* Description */}
        {desc && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <p className="text-gray-700 text-sm leading-relaxed">{desc}</p>
            {isTranslated && (
              <p className="text-xs text-gray-400 mt-3 flex items-center gap-1">
                🌐 {t('translated_from', { lang: 'Greek' })}
              </p>
            )}
          </div>
        )}

        {/* Services */}
        {salon.services.length > 0 && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <h2 className="font-semibold text-gray-800 mb-3">{t('services')}</h2>
            <div className="divide-y divide-gray-50">
              {salon.services.slice(0, 10).map(svc => (
                <div key={svc.id} className="py-2.5 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-800">{svc.name_el || svc.name}</p>
                    {svc.duration_min && <p className="text-xs text-gray-400">{svc.duration_min} λεπτά</p>}
                  </div>
                  {svc.price_from && (
                    <span className="text-sm font-medium text-gray-700">
                      {svc.price_to && svc.price_to !== svc.price_from
                        ? `${svc.price_from}–${svc.price_to}€`
                        : `${svc.price_from}€`}
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
            <h2 className="font-semibold text-gray-800 mb-3">{t('hours')}</h2>
            <SalonHours hours={salon.hours} locale={locale} />
          </div>
        )}

        {/* Social links */}
        {salon.social_links.length > 0 && (
          <div className="bg-white rounded-xl p-5 mb-4">
            <div className="flex flex-wrap gap-3">
              {salon.social_links.map(sl => <SocialLink key={sl.platform} platform={sl.platform} url={sl.url} />)}
            </div>
          </div>
        )}

        {/* Report */}
        <div className="text-center mt-6">
          <ReportButton salonId={salon.id} locale={locale} label={t('report')} />
        </div>
      </div>
    </div>
  );
}

function SocialLink({ platform, url }: { platform: string; url: string }) {
  const icons: Record<string, string> = {
    instagram: '📷', facebook: '👥', facebook_messenger: '💬',
    viber: '📲', whatsapp: '💬', tiktok: '🎵', youtube: '▶️',
  };
  const labels: Record<string, string> = {
    instagram: 'Instagram', facebook: 'Facebook', facebook_messenger: 'Messenger',
    viber: 'Viber', whatsapp: 'WhatsApp', tiktok: 'TikTok', youtube: 'YouTube',
  };
  return (
    <a href={url} target="_blank" rel="noopener noreferrer"
       className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-pink-600 border border-gray-100 px-3 py-1.5 rounded-full hover:border-pink-200 transition-colors">
      <span>{icons[platform] || '🔗'}</span>
      <span>{labels[platform] || platform}</span>
    </a>
  );
}
