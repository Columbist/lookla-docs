'use client';
import { usePathname, useRouter } from '@/i18n/navigation';

const LOCALES = ['el', 'en', 'ru', 'uk'] as const;

export default function LanguageSwitcher({ currentLocale }: { currentLocale: string }) {
  const router = useRouter();
  const pathname = usePathname();

  const switchLocale = (locale: string) => {
    router.replace(pathname, { locale });
  };

  return (
    <div className="flex justify-center gap-4 mt-2">
      {LOCALES.map(l => (
        <button
          key={l}
          onClick={() => switchLocale(l)}
          className={`uppercase text-sm ${l === currentLocale ? 'text-pink-600 font-medium' : 'text-gray-400 hover:text-gray-600'}`}
        >
          {l}
        </button>
      ))}
    </div>
  );
}
