'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';

export default function SearchBar({ locale }: { locale: string }) {
  const t = useTranslations('nav');
  const router = useRouter();
  const [q, setQ] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const path = locale === 'el' ? '/search' : `/${locale}/search`;
    router.push(`${path}?q=${encodeURIComponent(q)}`);
  };

  return (
    <form onSubmit={handleSearch} className="flex gap-2 max-w-xl mx-auto">
      <input
        type="text"
        value={q}
        onChange={e => setQ(e.target.value)}
        placeholder={t('search_placeholder')}
        className="flex-1 px-4 py-3 rounded-xl border border-gray-200 text-gray-800 focus:outline-none focus:ring-2 focus:ring-pink-300 text-sm"
      />
      <button
        type="submit"
        className="px-6 py-3 bg-pink-600 text-white rounded-xl font-medium hover:bg-pink-700 text-sm whitespace-nowrap"
      >
        🔍
      </button>
    </form>
  );
}
