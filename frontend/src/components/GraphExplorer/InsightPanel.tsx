import { useState } from 'react';
import { useAIInsight } from '../../hooks/useAIInsight';

interface InsightPanelProps {
  queryType: string;
  queryResults: unknown;
}

/** 마크다운 텍스트를 간단한 HTML로 변환 */
function renderMarkdown(text: string) {
  const lines = text.split('\n');
  const elements: JSX.Element[] = [];
  let key = 0;

  for (const line of lines) {
    key++;
    if (line.startsWith('### ')) {
      elements.push(<h4 key={key} className="font-semibold text-gray-800 mt-3 mb-1 text-sm">{line.slice(4)}</h4>);
    } else if (line.startsWith('## ')) {
      elements.push(<h3 key={key} className="font-bold text-gray-900 mt-4 mb-1.5 text-sm">{line.slice(3)}</h3>);
    } else if (line.startsWith('# ')) {
      elements.push(<h2 key={key} className="font-bold text-gray-900 mt-4 mb-2">{line.slice(2)}</h2>);
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      elements.push(
        <li key={key} className="text-gray-700 text-sm ml-4 list-disc">{renderInline(line.slice(2))}</li>
      );
    } else if (/^\d+\.\s/.test(line)) {
      const content = line.replace(/^\d+\.\s/, '');
      elements.push(
        <li key={key} className="text-gray-700 text-sm ml-4 list-decimal">{renderInline(content)}</li>
      );
    } else if (line.trim() === '') {
      elements.push(<div key={key} className="h-1.5" />);
    } else {
      elements.push(<p key={key} className="text-gray-700 text-sm leading-relaxed">{renderInline(line)}</p>);
    }
  }

  return elements;
}

/** 인라인 **bold** 처리 */
function renderInline(text: string): (string | JSX.Element)[] {
  const parts: (string | JSX.Element)[] = [];
  const regex = /\*\*(.*?)\*\*/g;
  let lastIdx = 0;
  let match;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.slice(lastIdx, match.index));
    }
    parts.push(<strong key={key++} className="font-semibold text-gray-900">{match[1]}</strong>);
    lastIdx = match.index + match[0].length;
  }
  if (lastIdx < text.length) {
    parts.push(text.slice(lastIdx));
  }
  return parts.length > 0 ? parts : [text];
}

export default function InsightPanel({ queryType, queryResults }: InsightPanelProps) {
  const { insight, isLoading, error, generate, clear } = useAIInsight();
  const [isExpanded, setIsExpanded] = useState(true);

  const handleGenerate = () => {
    generate(queryType, queryResults);
  };

  // 결과 없으면 표시 안함
  if (!queryResults) return null;

  return (
    <div className="card mt-4 border-l-4 border-l-purple-400">
      <div className="flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm font-semibold text-gray-700 hover:text-gray-900"
        >
          <svg className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          AI 분석
          {isLoading && (
            <span className="inline-flex items-center gap-1 text-xs text-purple-600 font-normal">
              <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-pulse" />
              생성 중...
            </span>
          )}
        </button>

        <div className="flex items-center gap-2">
          {insight && !isLoading && (
            <button
              onClick={() => navigator.clipboard.writeText(insight)}
              className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1"
              title="복사"
            >
              복사
            </button>
          )}
          {insight && (
            <button
              onClick={clear}
              className="text-xs text-gray-400 hover:text-red-500 px-2 py-1"
            >
              초기화
            </button>
          )}
          {!isLoading && (
            <button
              onClick={handleGenerate}
              className="px-3 py-1 text-xs font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-md transition-colors"
            >
              {insight ? '재생성' : '분석 생성'}
            </button>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="mt-3">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {isLoading && !insight && (
            <div className="space-y-2 animate-pulse">
              <div className="h-3 bg-gray-200 rounded w-3/4" />
              <div className="h-3 bg-gray-200 rounded w-full" />
              <div className="h-3 bg-gray-200 rounded w-5/6" />
              <div className="h-3 bg-gray-200 rounded w-2/3" />
            </div>
          )}

          {insight && (
            <div className="prose prose-sm max-w-none">
              {renderMarkdown(insight)}
              {isLoading && (
                <span className="inline-block w-2 h-4 bg-purple-500 animate-pulse ml-0.5" />
              )}
            </div>
          )}

          {!insight && !isLoading && !error && (
            <p className="text-xs text-gray-400">
              "분석 생성" 버튼을 클릭하면 AI가 쿼리 결과를 분석하여 인사이트를 제공합니다.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
