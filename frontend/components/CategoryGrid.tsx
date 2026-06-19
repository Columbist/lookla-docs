import Link from 'next/link';
import type { Category } from '@/lib/api';

const ICONS: Record<string, string> = {
  hair: '💇', nails: '💅', skin: '✨', waxing: '🪒',
  lashes_brows: '👁️', makeup: '💄', massage: '💆',
  barbershop: '✂️', tattoo_piercing: '🎨', spa: '🧖',
};

const NAMES: Record<string, Record<string, string>> = {
  el: { hair: 'Μαλλιά', nails: 'Νύχια', skin: 'Πρόσωπο & Δέρμα', waxing: 'Αποτρίχωση', lashes_brows: 'Βλεφαρίδες & Φρύδια', makeup: 'Μακιγιάζ', massage: 'Μασάζ & Σώμα', barbershop: 'Barbershop', tattoo_piercing: 'Τατουάζ', spa: 'Spa & Wellness' },
  en: { hair: 'Hair', nails: 'Nails', skin: 'Skin & Face', waxing: 'Waxing & Threading', lashes_brows: 'Lashes & Brows', makeup: 'Makeup', massage: 'Massage & Body', barbershop: 'Barbershop', tattoo_piercing: 'Tattoo & Piercing', spa: 'Spa & Wellness' },
  ru: { hair: 'Волосы', nails: 'Ногти', skin: 'Лицо и кожа', waxing: 'Эпиляция', lashes_brows: 'Ресницы и брови', makeup: 'Макияж', massage: 'Массаж и тело', barbershop: 'Барбершоп', tattoo_piercing: 'Тату и пирсинг', spa: 'Спа и велнес' },
  uk: { hair: 'Волосся', nails: 'Нігті', skin: 'Обличчя і шкіра', waxing: 'Епіляція', lashes_brows: 'Вії та брови', makeup: 'Макіяж', massage: 'Масаж і тіло', barbershop: 'Барбершоп', tattoo_piercing: 'Тату і пірсинг', spa: 'Спа і велнес' },
};

export default function CategoryGrid({ categories, locale }: { categories: Category[]; locale: string }) {
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const names = NAMES[locale] || NAMES.en;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
      {categories.slice(0, 10).map(cat => (
        <Link
          key={cat.slug}
          href={`${prefix}/search?category=${cat.slug}`}
          className="flex flex-col items-center p-5 bg-white border border-gray-100 rounded-2xl hover:border-pink-200 hover:shadow-sm transition-all text-center min-h-[96px] justify-center"
        >
          <span className="text-4xl mb-3">{ICONS[cat.slug] || '💈'}</span>
          <span className="text-sm text-gray-700 font-medium leading-tight">{names[cat.slug] || cat.name}</span>
        </Link>
      ))}
    </div>
  );
}
