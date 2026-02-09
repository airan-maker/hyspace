/**
 * Supplier Map
 * Leaflet 기반 소재/장비 공급처 지리공간 시각화
 */

import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getSupplierLocations, type SupplierLocation } from '../../services/api';

// Leaflet 기본 마커 아이콘 수정 (웹팩/Vite 이슈 해결)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#dc2626',
  HIGH: '#ea580c',
  MEDIUM: '#ca8a04',
  LOW: '#22c55e',
};

export default function SupplierMap() {
  const [suppliers, setSuppliers] = useState<SupplierLocation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    getSupplierLocations()
      .then(res => setSuppliers(res.suppliers))
      .catch(err => setError(err?.response?.data?.detail || '공급처 데이터 조회 실패'))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[500px]">
        <div className="animate-spin w-8 h-8 border-4 border-nexus-200 border-t-nexus-600 rounded-full" />
        <span className="ml-3 text-gray-500">지도 데이터 로딩 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[500px] text-red-500 text-sm">
        {error}
      </div>
    );
  }

  if (suppliers.length === 0) {
    return (
      <div className="flex items-center justify-center h-[500px] text-gray-500 text-sm">
        공급처 위치 데이터가 없습니다. 온톨로지 마이그레이션을 먼저 실행하세요.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <MapContainer
        center={[30, 100]}
        zoom={2}
        style={{ height: '500px', width: '100%', borderRadius: '0.5rem' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {suppliers.map((s, i) => {
          const riskColor = RISK_COLORS[s.risk || ''] || RISK_COLORS[s.criticality || ''] || '#6b7280';

          return (
            <CircleMarker
              key={i}
              center={[s.lat, s.lng]}
              radius={8}
              pathOptions={{
                color: riskColor,
                fillColor: riskColor,
                fillOpacity: 0.7,
                weight: 2,
              }}
            >
              <Popup>
                <div className="text-xs space-y-1 min-w-[160px]">
                  <p className="font-bold text-sm">{s.vendor}</p>
                  <p className="text-gray-500">{s.city}, {s.country}</p>
                  <hr className="border-gray-200" />
                  <p><span className="text-gray-400">제품:</span> {s.node_name}</p>
                  <p><span className="text-gray-400">유형:</span> {s.node_label}</p>
                  {s.risk && (
                    <p>
                      <span className="text-gray-400">공급 리스크:</span>{' '}
                      <span style={{ color: RISK_COLORS[s.risk] || '#6b7280' }} className="font-medium">{s.risk}</span>
                    </p>
                  )}
                  {s.criticality && (
                    <p>
                      <span className="text-gray-400">중요도:</span>{' '}
                      <span className="font-medium">{s.criticality}</span>
                    </p>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* 범례 */}
      <div className="flex items-center justify-center gap-6 text-xs">
        {Object.entries(RISK_COLORS).map(([level, color]) => (
          <div key={level} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-gray-600">{level}</span>
          </div>
        ))}
      </div>

      {/* 공급처 요약 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Object.entries(
          suppliers.reduce<Record<string, number>>((acc, s) => {
            acc[s.country] = (acc[s.country] || 0) + 1;
            return acc;
          }, {})
        )
          .sort(([, a], [, b]) => b - a)
          .map(([country, count]) => (
            <div key={country} className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500">{country}</p>
              <p className="text-lg font-semibold text-gray-800">{count}</p>
              <p className="text-[10px] text-gray-400">공급처</p>
            </div>
          ))}
      </div>
    </div>
  );
}
