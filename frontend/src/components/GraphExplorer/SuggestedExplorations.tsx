/**
 * Suggested Explorations
 * 카테고리별 추천 질의 카드 (탐색 탭)
 */

import { SUGGESTED_EXPLORATIONS } from './constants';

const CATEGORY_ICONS: Record<string, JSX.Element> = {
  shield: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  cog: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  link: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  ),
};

interface Props {
  onExecute: (presetId: string) => void;
  selectedQuery: string;
  isLoading: boolean;
}

export default function SuggestedExplorations({ onExecute, selectedQuery, isLoading }: Props) {
  return (
    <div className="space-y-4">
      {SUGGESTED_EXPLORATIONS.map((cat) => (
        <div key={cat.category}>
          <div className="flex items-center gap-2 mb-2">
            <span style={{ color: cat.color }}>{CATEGORY_ICONS[cat.icon]}</span>
            <h4 className="text-xs font-semibold text-gray-600">{cat.category}</h4>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {cat.queries.map((q) => (
              <button
                key={q.presetId}
                onClick={() => onExecute(q.presetId)}
                disabled={isLoading}
                className={`text-left p-3 rounded-lg border transition-all ${
                  selectedQuery === q.presetId
                    ? 'border-nexus-500 bg-nexus-50 ring-1 ring-nexus-500'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                } disabled:opacity-50`}
              >
                <div className="text-sm font-medium text-gray-800">{q.title}</div>
                <div className="text-xs text-gray-500 mt-0.5 line-clamp-2">{q.desc}</div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
