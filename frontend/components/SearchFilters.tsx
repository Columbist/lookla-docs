'use client';
import { useRouter, usePathname } from 'next/navigation';
import type { City, Category } from '@/lib/api';

interface Props {
  locale: string;
  cities: City[];
  categories: Category[];
  current: Record<string, string | undefined>;
}

export default function SearchFilters({ locale, cities, categories, current }: Props) {
  const router = useRouter();
  const pathname = usePathname();

  const update = (key: string, value: string) => {
    const params = new URLSearchParams(current as Record<string, string>);
    if (value) params.set(key, value); else params.delete(key);
    router.push(`${pathname}?${params}`);
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <input
        type="text"
        defaultValue={current.q}
        placeholder="Αναζήτηση..."
        onKeyDown={e => e.key === 'Enter' && update('q', (e.target as HTMLInputElement).value)}
        className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-pink-300 w-40"
      />
      <select
        value={current.city || ''}
        onChange={e => update('city', e.target.value)}
        className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-pink-300"
      >
        <option value="">Πόλη</option>
        {cities.slice(0, 20).map(c => (
          <option key={c.city} value={c.city}>{c.city} ({c.count})</option>
        ))}
      </select>
      <select
        value={current.category || ''}
        onChange={e => update('category', e.target.value)}
        className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-pink-300"
      >
        <option value="">Κατηγορία</option>
        {categories.map(c => (
          <option key={c.slug} value={c.slug}>{c.name}</option>
        ))}
      </select>
    </div>
  );
}
