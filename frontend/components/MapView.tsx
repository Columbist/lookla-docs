'use client';
import { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import type { SalonListItem } from '@/lib/api';

const TILES: Record<string, { url: string; attribution: string }> = {
  el: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  },
  default: {
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="https://carto.com/">CARTO</a>',
  },
};

function getTiles(locale: string) {
  return TILES[locale] ?? TILES.default;
}

function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

const NEARBY_KM = 15;
const NEARBY_ZOOM = 13;
const DEFAULT_CENTER: [number, number] = [37.9838, 23.7275];
const DEFAULT_ZOOM = 10;

interface Props {
  salons: SalonListItem[];
  locale: string;
}

export default function MapView({ salons, locale }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const layerGroupRef = useRef<any>(null);
  const leafletRef = useRef<any>(null);
  const userPosRef = useRef<[number, number] | null>(null);
  const [selected, setSelected] = useState<SalonListItem | null>(null);
  const [locating, setLocating] = useState(true);
  const t = useTranslations('salon');
  const prefix = locale === 'el' ? '' : `/${locale}`;

  const buildIcon = (L: any) =>
    L.divIcon({
      html: `<div style="background:#db2777;width:10px;height:10px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3)"></div>`,
      className: '',
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    });

  const getVisibleSalons = (all: SalonListItem[]): SalonListItem[] => {
    const pos = userPosRef.current;
    if (!pos) return all;
    return all.filter(s => s.lat && s.lng && haversineKm(pos[0], pos[1], s.lat!, s.lng!) <= NEARBY_KM);
  };

  const refreshMarkers = (L: any, visible: SalonListItem[]) => {
    if (!layerGroupRef.current) return;
    layerGroupRef.current.clearLayers();
    const icon = buildIcon(L);
    visible.filter(s => s.lat && s.lng).forEach(salon => {
      L.marker([salon.lat!, salon.lng!], { icon })
        .on('click', () => setSelected(salon))
        .addTo(layerGroupRef.current);
    });
  };

  // Init map once, then try geolocation
  useEffect(() => {
    if (typeof window === 'undefined' || !mapRef.current) return;
    if (mapInstanceRef.current) return;

    import('leaflet').then(L => {
      if (!mapRef.current || mapInstanceRef.current) return;
      leafletRef.current = L;

      const map = L.map(mapRef.current, { center: DEFAULT_CENTER, zoom: DEFAULT_ZOOM });
      const tiles = getTiles(locale);
      L.tileLayer(tiles.url, { attribution: tiles.attribution, maxZoom: 19 }).addTo(map);
      layerGroupRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;

      // Show all salons initially (before geolocation resolves)
      refreshMarkers(L, salons);

      // Try geolocation — only on initial open
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            const { latitude, longitude } = pos.coords;
            userPosRef.current = [latitude, longitude];

            // Center on user at district level
            map.setView([latitude, longitude], NEARBY_ZOOM);

            // "You are here" marker
            L.circleMarker([latitude, longitude], {
              radius: 8,
              color: '#2563eb',
              fillColor: '#3b82f6',
              fillOpacity: 0.9,
              weight: 2,
            }).bindTooltip('📍 Η θέση σας', { permanent: false }).addTo(map);

            // Show only nearby salons
            refreshMarkers(L, getVisibleSalons(salons));
            setLocating(false);
          },
          () => {
            // Denied or unavailable — keep default Athens view with all salons
            setLocating(false);
          },
          { timeout: 6000, maximumAge: 60000 }
        );
      } else {
        setLocating(false);
      }
    });

    return () => {
      mapInstanceRef.current?.remove();
      mapInstanceRef.current = null;
      layerGroupRef.current = null;
      leafletRef.current = null;
      userPosRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Update markers when salons list changes (filter changes)
  useEffect(() => {
    if (!leafletRef.current || !layerGroupRef.current) return;
    refreshMarkers(leafletRef.current, getVisibleSalons(salons));
    setSelected(null);
  }, [salons]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="relative">
      {locating && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[1000] bg-white/90 text-xs text-gray-600 px-3 py-1.5 rounded-full shadow-sm">
          📍 Εντοπισμός τοποθεσίας...
        </div>
      )}
      <div ref={mapRef} className="w-full rounded-xl overflow-hidden" style={{ height: '60vh', minHeight: 400 }} />

      {selected && (
        <div className="absolute bottom-4 left-4 right-4 bg-white rounded-xl shadow-lg p-4 z-[1000]">
          <button
            onClick={() => setSelected(null)}
            className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 text-lg leading-none"
          >
            ×
          </button>
          <div className="flex gap-3">
            {selected.primary_photo && (
              <img
                src={selected.primary_photo}
                alt={selected.name}
                className="w-16 h-16 object-cover rounded-lg flex-shrink-0"
              />
            )}
            <div className="min-w-0">
              <h3 className="font-semibold text-gray-900 text-sm leading-tight">{selected.name}</h3>
              <p className="text-xs text-gray-500 mt-0.5">{selected.address_city}</p>
              {selected.rating_google && (
                <p className="text-xs text-yellow-500 mt-1">
                  ★ {parseFloat(selected.rating_google).toFixed(1)}
                </p>
              )}
              <div className="flex gap-2 mt-2">
                {selected.phone_primary && (
                  <a
                    href={`tel:${selected.phone_primary}`}
                    className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-lg"
                  >
                    📞
                  </a>
                )}
                <a
                  href={`${prefix}/salons/${selected.slug || selected.id}`}
                  className="text-xs bg-pink-600 text-white px-3 py-1 rounded-lg font-medium"
                >
                  {t('view')}
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
