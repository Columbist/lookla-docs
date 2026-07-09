import { redirect } from 'next/navigation';

export default function PricingPage({ params }: { params: { locale: string } }) {
  const locale = (params as any).locale ?? 'el';
  redirect(locale === 'el' ? '/' : `/${locale}`);
}
