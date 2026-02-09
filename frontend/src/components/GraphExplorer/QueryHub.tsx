/**
 * QueryHub
 * 통합 질의 인터페이스 — 탐색 / 템플릿 / Cypher 3탭
 */

import { useState } from 'react';
import SearchBar from './SearchBar';
import SuggestedExplorations from './SuggestedExplorations';
import QueryTemplates from './QueryTemplates';
import type { SearchResultNode } from '../../services/api';

type TabId = 'explore' | 'templates' | 'cypher';

interface Props {
  onExecutePreset: (presetId: string) => void;
  onExecuteTemplate: (templateId: string, params: Record<string, string>) => void;
  onExecuteCypher: (cypher: string) => void;
  onNodeSelect: (node: SearchResultNode) => void;
  isLoading: boolean;
  selectedQuery: string;
}

const TABS: { id: TabId; label: string; desc: string }[] = [
  { id: 'explore', label: '탐색', desc: '추천 질의로 빠르게 시작' },
  { id: 'templates', label: '템플릿', desc: '파라미터를 선택하여 질의' },
  { id: 'cypher', label: 'Cypher', desc: '고급 질의 직접 입력' },
];

function CypherInput({ onExecute, isLoading }: { onExecute: (cypher: string) => void; isLoading: boolean }) {
  const [cypher, setCypher] = useState('');

  return (
    <div>
      <p className="text-xs text-gray-500 mb-2">
        Neo4j Cypher 쿼리를 직접 입력합니다. 그래프 구조에 익숙한 사용자를 위한 고급 기능입니다.
      </p>
      <div className="flex gap-2">
        <input
          type="text"
          value={cypher}
          onChange={(e) => setCypher(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && cypher.trim()) onExecute(cypher); }}
          placeholder="MATCH (n:AIAccelerator) RETURN n.name, n.tdp_watts LIMIT 10"
          className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-nexus-500 focus:border-nexus-500 font-mono"
        />
        <button
          onClick={() => { if (cypher.trim()) onExecute(cypher); }}
          disabled={isLoading || !cypher.trim()}
          className="px-4 py-2 text-sm bg-gray-800 text-white rounded-lg hover:bg-gray-900 disabled:opacity-50"
        >
          실행
        </button>
      </div>
    </div>
  );
}

export default function QueryHub({
  onExecutePreset,
  onExecuteTemplate,
  onExecuteCypher,
  onNodeSelect,
  isLoading,
  selectedQuery,
}: Props) {
  const [activeTab, setActiveTab] = useState<TabId>('explore');

  return (
    <div className="card mb-6">
      {/* SearchBar */}
      <SearchBar onNodeSelect={onNodeSelect} />

      {/* Tab Headers */}
      <div className="flex items-center gap-1 mt-4 mb-3 border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-2 text-sm transition-colors relative ${
              activeTab === tab.id
                ? 'text-nexus-700 font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
            {activeTab === tab.id && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-nexus-600 rounded-t" />
            )}
          </button>
        ))}
        <span className="ml-auto text-[11px] text-gray-400">
          {TABS.find(t => t.id === activeTab)?.desc}
        </span>
      </div>

      {/* Tab Content */}
      {activeTab === 'explore' && (
        <SuggestedExplorations
          onExecute={onExecutePreset}
          selectedQuery={selectedQuery}
          isLoading={isLoading}
        />
      )}
      {activeTab === 'templates' && (
        <QueryTemplates
          onExecuteTemplate={onExecuteTemplate}
          isLoading={isLoading}
        />
      )}
      {activeTab === 'cypher' && (
        <CypherInput onExecute={onExecuteCypher} isLoading={isLoading} />
      )}
    </div>
  );
}
