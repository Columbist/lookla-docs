// Server-side: call backend directly. Client-side: via nginx proxy.
const API_BASE = typeof window === 'undefined'
  ? (process.env.API_INTERNAL_URL || 'http://localhost:8001/api')
  : '/api';

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    cache: 'no-store',
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

// Typed helpers
export const api = {
  salons: {
    list: (params: Record<string, string | number | boolean>) => {
      const q = new URLSearchParams(Object.entries(params).map(([k,v]) => [k, String(v)]));
      return apiFetch<SalonListResponse>(`/salons?${q}`);
    },
    get: (slug: string) => apiFetch<SalonDetail>(`/salons/${slug}`),
    photos: (id: number) => apiFetch<Photo[]>(`/salons/${id}/photos`),
  },
  professionals: {
    list: (params: Record<string, string | number | boolean>) => {
      const q = new URLSearchParams(Object.entries(params).map(([k,v]) => [k, String(v)]));
      return apiFetch<ProfessionalListResponse>(`/professionals?${q}`);
    },
    get: (slug: string) => apiFetch<ProfessionalDetail>(`/professionals/${slug}`),
  },
  search: (params: Record<string, string | number>) => {
    const q = new URLSearchParams(Object.entries(params).map(([k,v]) => [k, String(v)]));
    return apiFetch<SearchResult[]>(`/search?${q}`);
  },
  cities: () => apiFetch<City[]>('/cities'),
  categories: (lang = 'el') => apiFetch<Category[]>(`/categories?lang=${lang}`),
};

// Types
export interface SalonListItem {
  id: number; name: string; slug?: string;
  address_city?: string; address_street?: string; address_number?: string;
  lat?: number; lng?: number; phone_primary?: string;
  rating_google?: string; rating_count: number; price_level?: number;
  is_verified: boolean; primary_photo?: string;
  min_price?: number; is_open_now?: boolean;
}
export interface SalonHour { day_of_week: number; open_time?: string; close_time?: string; is_closed: boolean; }
export interface Photo { id: number; url: string; caption?: string; is_primary: boolean; width?: number; height?: number; }
export interface ServiceItem { id: number; name: string; name_el?: string; description?: string; duration_min?: number; price_from?: string; price_to?: string; currency: string; }
export interface SocialLink { platform: string; url: string; }
export interface ReviewItem { id: number; source: string; author_name?: string; rating?: number; text?: string; published_at?: string; }
export interface SalonDetail extends SalonListItem {
  name_el?: string; description?: string; description_el?: string; description_ru?: string; description_uk?: string;
  address_full?: string; address_region?: string; address_postal?: string; email?: string; website?: string;
  data_verified_at?: string;
  hours: SalonHour[]; photos: Photo[]; services: ServiceItem[]; social_links: SocialLink[];
  reviews: ReviewItem[];
  review_count: number;
}
export interface SalonListResponse { items: SalonListItem[]; total: number; page: number; limit: number; pages: number; }
export interface PortfolioItem { id: number; url_after: string; url_before?: string; caption?: string; service_tag?: string; is_featured: boolean; }
export interface AvailSlot { day_of_week: number; start_time?: string; end_time?: string; is_available: boolean; }
export interface ProfessionalListItem {
  id: number; name: string; slug?: string; specialty?: string;
  base_city?: string; base_lat?: number; base_lng?: number;
  service_radius_km: number; does_home_visits: boolean; has_home_studio: boolean;
  phone?: string; rating_avg?: string; review_count: number; price_level?: number;
  is_verified: boolean; featured_photo?: string; distance_km?: number;
}
export interface ProfessionalDetail extends ProfessionalListItem {
  bio?: string; bio_el?: string; bio_ru?: string; bio_uk?: string;
  instagram?: string; email?: string;
  portfolio: PortfolioItem[]; availability: AvailSlot[]; social_links: SocialLink[];
}
export interface ProfessionalListResponse { items: ProfessionalListItem[]; total: number; page: number; limit: number; pages: number; }
export interface SearchResult {
  type: string; id: number; name: string; slug?: string;
  address_city?: string; lat?: number; lng?: number; phone_primary?: string;
  rating_google?: string; price_level?: number; primary_photo?: string; distance_km?: number;
}
export interface City { city: string; count: number; }
export interface Category { id: number; slug: string; name: string; name_en: string; parent_id?: number; icon?: string; children: Category[]; }
