import { defineRouting } from 'next-intl/routing';
export const routing = defineRouting({
  locales: ['el', 'en', 'ru', 'uk'],
  defaultLocale: 'el',
  localePrefix: 'as-needed', // /el omitted (default), /en/..., /ru/...
});
