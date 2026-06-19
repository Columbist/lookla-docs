import { api } from '@/lib/api';
import type { Metadata } from 'next';
import SalonDetailClient from './SalonDetailClient';

interface Props {
  params: { locale: string; slug: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const slug = (params as any).slug;
  const salon = await api.salons.get(slug).catch(() => null);
  if (!salon) return { title: 'Lookla' };
  return {
    title: salon.name,
    description: salon.description?.slice(0, 160) || `${salon.name} — ${salon.address_city}`,
    openGraph: { images: salon.primary_photo ? [salon.primary_photo] : [] },
  };
}

export default async function SalonPage({ params }: Props) {
  const locale = (params as any).locale ?? 'el';
  const slug = (params as any).slug;
  const salon = await api.salons.get(slug).catch(() => null);
  return <SalonDetailClient salon={salon} locale={locale} slug={slug} />;
}
