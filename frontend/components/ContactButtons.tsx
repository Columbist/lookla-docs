'use client';
import type { SalonDetail } from '@/lib/api';

interface Props {
  salon: SalonDetail;
  locale: string;
  t_call: string; t_viber: string; t_whatsapp: string; t_website: string;
  t_message: string; t_book: string; t_request: string;
}

export default function ContactButtons({ salon, locale, t_call, t_viber, t_whatsapp, t_website, t_message, t_book, t_request }: Props) {
  const phone = salon.phone_primary?.replace(/\s/g, '');
  const e164 = phone ? (phone.startsWith('+') ? phone.replace(/\D/g, '') : `30${phone.replace(/\D/g, '')}`) : null;
  const prefix = locale === 'el' ? '' : `/${locale}`;

  const viberLink = salon.social_links?.find(sl => sl.platform === 'viber')?.url
    || (e164 ? `viber://chat?number=+${e164}` : null);
  const waLink = salon.social_links?.find(sl => sl.platform === 'whatsapp')?.url
    || (e164 ? `https://wa.me/${e164}` : null);

  return (
    <div className="space-y-2">
      {/* Primary: Book + Request */}
      <div className="flex gap-2">
        <button className="flex-1 py-2.5 bg-pink-600 text-white rounded-xl text-sm font-semibold hover:bg-pink-700 transition-colors">
          📅 {t_book}
        </button>
        <button className="flex-1 py-2.5 border border-pink-200 text-pink-600 rounded-xl text-sm font-medium hover:bg-pink-50 transition-colors">
          ⏰ {t_request}
        </button>
      </div>

      {/* Secondary: call, viber, whatsapp, message */}
      <div className="flex gap-2 flex-wrap">
        {phone && (
          <a href={`tel:${phone}`}
             className="flex items-center gap-1.5 px-3 py-2 bg-green-50 text-green-700 rounded-xl text-sm font-medium hover:bg-green-100">
            📞 {t_call}
          </a>
        )}
        {viberLink && (
          <a href={viberLink}
             className="flex items-center gap-1.5 px-3 py-2 bg-purple-50 text-purple-700 rounded-xl text-sm font-medium hover:bg-purple-100">
            📲 {t_viber}
          </a>
        )}
        {waLink && (
          <a href={waLink} target="_blank" rel="noopener noreferrer"
             className="flex items-center gap-1.5 px-3 py-2 bg-emerald-50 text-emerald-700 rounded-xl text-sm font-medium hover:bg-emerald-100">
            💬 {t_whatsapp}
          </a>
        )}
        {salon.website && (
          <a href={salon.website} target="_blank" rel="noopener noreferrer"
             className="flex items-center gap-1.5 px-3 py-2 bg-blue-50 text-blue-700 rounded-xl text-sm font-medium hover:bg-blue-100">
            🌐 {t_website}
          </a>
        )}
        <button className="flex items-center gap-1.5 px-3 py-2 bg-gray-50 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-100">
          ✉️ {t_message}
        </button>
      </div>
    </div>
  );
}
