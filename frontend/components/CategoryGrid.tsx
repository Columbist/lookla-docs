import Link from 'next/link';
import type { Category } from '@/lib/api';

const ICONS: Record<string, string> = {
  hair: '💇', nails: '💅', skin: '✨', waxing: '🪒',
  lashes_brows: '👁️', makeup: '💄', massage: '💆',
  barbershop: '✂️', tattoo_piercing: '🎨', spa: '🧖',
};

export default function CategoryGrid({ categories, locale }: { categories: Category[]; locale: string }) {
  const prefix = locale === 'el' ? '' : `/${locale}`;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
      {categories.slice(0, 10).map(cat => (
        <Link
          key={cat.slug}
          href={`${prefix}/search?category=${cat.slug}`}
          className="flex flex-col items-center p-4 bg-white border border-gray-100 rounded-xl hover:border-pink-200 hover:shadow-sm transition-all text-center"
        >
          <span className="text-2xl mb-2">{ICONS[cat.slug] || '💈'}</span>
          <span className="text-xs text-gray-700 font-medium leading-tight">{cat.name}</span>
        </Link>
      ))}
    </div>
  );
}
