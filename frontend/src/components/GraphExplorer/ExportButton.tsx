/**
 * Export Button
 * 그래프 캔버스를 PNG/SVG로 내보내기
 */

import { useState } from 'react';

interface Props {
  graphRef?: React.RefObject<any>;
}

export default function ExportButton({ graphRef }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  const exportPNG = () => {
    // react-force-graph-2d의 내부 canvas 찾기
    const canvas = document.querySelector('.force-graph-container canvas') as HTMLCanvasElement
      || document.querySelector('canvas');
    if (!canvas) return;

    const link = document.createElement('a');
    link.download = `silicon-nexus-graph-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    setIsOpen(false);
  };

  const exportJSON = () => {
    if (!graphRef?.current) return;
    const data = graphRef.current.graphData?.() || {};
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.download = `silicon-nexus-graph-${Date.now()}.json`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
    setIsOpen(false);
  };

  return (
    <div className="relative inline-flex">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
        title="내보내기"
      >
        <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1 z-30 bg-white border border-gray-200 rounded-lg shadow-lg w-40">
          <button
            onClick={exportPNG}
            className="w-full text-left px-3 py-2 text-xs hover:bg-gray-50 flex items-center gap-2"
          >
            <span className="text-gray-400">PNG</span>
            <span className="text-gray-700">이미지 저장</span>
          </button>
          <button
            onClick={exportJSON}
            className="w-full text-left px-3 py-2 text-xs hover:bg-gray-50 flex items-center gap-2 border-t border-gray-50"
          >
            <span className="text-gray-400">JSON</span>
            <span className="text-gray-700">데이터 내보내기</span>
          </button>
        </div>
      )}
    </div>
  );
}
