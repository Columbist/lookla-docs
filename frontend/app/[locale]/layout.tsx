import { NextIntlClientProvider } from 'next-intl';
import { getMessages, getLocale } from 'next-intl/server';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import '../globals.css';

export const metadata: Metadata = {
  title: { default: 'Lookla — Κομμωτήρια & Σαλόνια Ελλάδα', template: '%s | Lookla' },
  description: 'Βρείτε κομμωτήρια, σαλόνια νυχιών, ιδιωτικούς επαγγελματίες σε όλη την Ελλάδα.',
};

const locales = ['el', 'en', 'ru', 'uk'];

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const { locale } = await params;
  if (!locales.includes(locale)) notFound();
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
