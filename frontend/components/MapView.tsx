'use client';
import { useEffect, useRef, useState } from 'react';
import type { SalonListItem } from '@/lib/api';

interface Props {
  salons: SalonListItem[];
  locale: string;
}

export default function MapView({ salons, locale }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const [selected, setSelected] = useState<SalonListItem | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !mapRef.current) return;
    if (mapInstanceRef.current) return; // already initialized

    // Dynamic import to avoid SSR issues
    import('leaflet').then(L => {

      const map = L.map(mapRef.current!, {
        center: [37.9838, 23.7275],
        zoom: 11,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      // Custom pink marker
      const pinkIcon = L.divIcon({
        html: `<div style="background:#db2777;width:10px;height:10px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.3)"></div>`,
        className: '',
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      salons.filter(s => s.lat && s.lng).forEach(salon => {
        const marker = L.marker([salon.lat!, salon.lng!], { icon: pinkIcon })
          .addTo(map)
          .on('click', () => setSelected(salon));
      });

      mapInstanceRef.current = map;
    });

    return () => {
      mapInstanceRef.current?.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  const prefix = locale === 'el' ? '' : `/${locale}`;

  return (
    <div className="relative">
      <div ref={mapRef} className="w-full rounded-xl overflow-hidden" style={{ height: '60vh', minHeight: 400 }} />

      {/* Bottom sheet for selected salon */}
      {selected && (
        <div className="absolute bottom-4 left-4 right-4 bg-white rounded-xl shadow-lg p-4 z-[1000]">
          <button onClick={() => setSelected(null)} className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
          <div className="flex gap-3">
            {selected.primary_photo && (
              <img src={selected.primary_photo} alt={selected.name} className="w-16 h-16 object-cover rounded-lg flex-shrink-0" />
            )}
            <div className="min-w-0">
              <h3 className="font-semibold text-gray-900 text-sm leading-tight">{selected.name}</h3>
              <p className="text-xs text-gray-500 mt-0.5">{selected.address_city}</p>
              {selected.rating_google && (
                <p className="text-xs text-yellow-500 mt-1">★ {parseFloat(selected.rating_google).toFixed(1)}</p>
              )}
              <div className="flex gap-2 mt-2">
                {selected.phone_primary && (
                  <a href={`tel:${selected.phone_primary}`} className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-lg">📞</a>
                )}
                <a href={`${prefix}/salons/${selected.slug || selected.id}`}
                   className="text-xs bg-pink-600 text-white px-3 py-1 rounded-lg font-medium">
                  Προφίλ →
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
