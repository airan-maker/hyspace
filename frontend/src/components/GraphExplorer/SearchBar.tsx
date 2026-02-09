/**
 * Graph Search Bar
 * 디바운스 검색 + 필터 칩 + 자동완성 드롭다운
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { searchGraphNodes, getGraphLabels, type SearchResultNode } from '../../services/api';
import { LABEL_COLORS } from './constants';

interface Props {
  onNodeSelect: (node: SearchResultNode) => void;
}

export default function SearchBar({ onNodeSelect }: Props) {
  const [query, setQuery] = useState('');
  const [labelFilter, setLabelFilter] = useState<string | null>(null);
  const [riskFilter, setRiskFilter] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResultNode[]>([]);
  const [labels, setLabels] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // 라벨 목록 로드
  useEffect(() => {
    getGraphLabels().then(res => setLabels(res.labels)).catch(() => {});
  }, []);

  // 외부 클릭 시 닫기
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const doSearch = useCallback(async (q: string, label: string | null, risk: string | null) => {
    if (!q && !label && !risk) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);
    try {
      const res = await searchGraphNodes({
        q: q || undefined,
        label: label || undefined,
        risk: risk || undefined,
        limit: 15,
      });
      setResults(res.results);
      setIsOpen(true);
    } catch {
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 디바운스 검색
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      doSearch(query, labelFilter, riskFilter);
    }, 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, labelFilter, riskFilter, doSearch]);

  const handleSelect = (node: SearchResultNode) => {
    onNodeSelect(node);
    setIsOpen(false);
    setQuery('');
  };

  const RISK_LEVELS = ['HIGH', 'CRITICAL', 'MEDIUM', 'LOW'];

  return (
    <div ref={containerRef} className="card mb-4 relative">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">노드 검색</h3>

      {/* 검색 입력 */}
      <div className="flex gap-2 mb-2">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => { if (results.length > 0) setIsOpen(true); }}
            placeholder="노드 이름, 벤더, 카테고리 검색..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-nexus-500 focus:border-nexus-500"
          />
          {isLoading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="animate-spin w-4 h-4 border-2 border-gray-300 border-t-nexus-600 rounded-full" />
            </div>
          )}
        </div>
      </div>

      {/* 필터 칩 */}
      <div className="flex flex-wrap gap-1.5">
        {/* 라벨 필터 */}
        {labels.map(l => (
          <button
            key={l}
            onClick={() => setLabelFilter(prev => prev === l ? null : l)}
            className={`px-2 py-0.5 text-[11px] rounded-full border transition-colors ${
              labelFilter === l
                ? 'text-white border-transparent'
                : 'text-gray-600 border-gray-200 hover:border-gray-300'
            }`}
            style={labelFilter === l ? { backgroundColor: LABEL_COLORS[l] || '#6b7280' } : undefined}
          >
            {l}
          </button>
        ))}

        {/* 구분선 */}
        {labels.length > 0 && <span className="text-gray-300 self-center">|</span>}

        {/* 리스크 필터 */}
        {RISK_LEVELS.map(r => {
          const colors: Record<string, string> = { CRITICAL: '#dc2626', HIGH: '#ea580c', MEDIUM: '#ca8a04', LOW: '#2563eb' };
          return (
            <button
              key={r}
              onClick={() => setRiskFilter(prev => prev === r ? null : r)}
              className={`px-2 py-0.5 text-[11px] rounded-full border transition-colors ${
                riskFilter === r
                  ? 'text-white border-transparent'
                  : 'text-gray-600 border-gray-200 hover:border-gray-300'
              }`}
              style={riskFilter === r ? { backgroundColor: colors[r] } : undefined}
            >
              {r}
            </button>
          );
        })}

        {/* 클리어 */}
        {(labelFilter || riskFilter) && (
          <button
            onClick={() => { setLabelFilter(null); setRiskFilter(null); }}
            className="px-2 py-0.5 text-[11px] text-gray-400 hover:text-gray-600"
          >
            초기화
          </button>
        )}
      </div>

      {/* 드롭다운 결과 */}
      {isOpen && results.length > 0 && (
        <div className="absolute left-0 right-0 top-full mt-1 z-20 bg-white border border-gray-200 rounded-lg shadow-lg max-h-72 overflow-y-auto">
          {results.map((node, i) => (
            <button
              key={i}
              onClick={() => handleSelect(node)}
              className="w-full text-left px-4 py-2.5 hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0"
            >
              <div className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: LABEL_COLORS[node.label] || '#9ca3af' }}
                />
                <span className="text-sm font-medium text-gray-800">{node.name}</span>
                <span className="text-[10px] text-gray-400">{node.label}</span>
                <span className="ml-auto text-[10px] text-gray-400">
                  {node.connection_count} connections
                </span>
              </div>
              {/* 주요 속성 미리보기 */}
              <div className="ml-[18px] mt-0.5 flex gap-3 text-[10px] text-gray-500">
                {node.properties.vendor && <span>vendor: {String(node.properties.vendor)}</span>}
                {node.properties.supply_risk && (
                  <span className="text-red-500">risk: {String(node.properties.supply_risk)}</span>
                )}
                {node.properties.criticality && (
                  <span className="text-orange-500">criticality: {String(node.properties.criticality)}</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {isOpen && results.length === 0 && (query || labelFilter || riskFilter) && !isLoading && (
        <div className="absolute left-0 right-0 top-full mt-1 z-20 bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-center text-sm text-gray-500">
          검색 결과가 없습니다
        </div>
      )}
    </div>
  );
}
