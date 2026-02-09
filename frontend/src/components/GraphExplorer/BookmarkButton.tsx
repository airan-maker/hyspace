/**
 * Bookmark Button + List
 * 로컬스토리지 기반 그래프 질의 북마크
 */

import { useState, useEffect } from 'react';

interface Bookmark {
  id: string;
  queryId: string;
  label: string;
  memo: string;
  createdAt: string;
}

const STORAGE_KEY = 'silicon-nexus-graph-bookmarks';

function loadBookmarks(): Bookmark[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveBookmarks(bookmarks: Bookmark[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
}

interface Props {
  currentQueryId: string;
  currentQueryLabel: string;
  onLoadBookmark: (queryId: string) => void;
}

export default function BookmarkButton({ currentQueryId, currentQueryLabel, onLoadBookmark }: Props) {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [memo, setMemo] = useState('');
  const [showAdd, setShowAdd] = useState(false);

  useEffect(() => {
    setBookmarks(loadBookmarks());
  }, []);

  const isBookmarked = bookmarks.some(b => b.queryId === currentQueryId);

  const addBookmark = () => {
    if (!currentQueryId) return;
    const newBookmark: Bookmark = {
      id: Date.now().toString(),
      queryId: currentQueryId,
      label: currentQueryLabel || currentQueryId,
      memo,
      createdAt: new Date().toISOString(),
    };
    const updated = [newBookmark, ...bookmarks];
    setBookmarks(updated);
    saveBookmarks(updated);
    setShowAdd(false);
    setMemo('');
  };

  const removeBookmark = (id: string) => {
    const updated = bookmarks.filter(b => b.id !== id);
    setBookmarks(updated);
    saveBookmarks(updated);
  };

  return (
    <div className="relative inline-flex">
      {/* 북마크 추가 버튼 */}
      {currentQueryId && (
        <button
          onClick={() => {
            if (isBookmarked) {
              const bm = bookmarks.find(b => b.queryId === currentQueryId);
              if (bm) removeBookmark(bm.id);
            } else {
              setShowAdd(true);
            }
          }}
          className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
          title={isBookmarked ? '북마크 해제' : '북마크 추가'}
        >
          <svg className={`w-4 h-4 ${isBookmarked ? 'text-yellow-500 fill-yellow-500' : 'text-gray-400'}`} viewBox="0 0 24 24" stroke="currentColor" fill="none" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </button>
      )}

      {/* 북마크 목록 토글 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-1.5 rounded-md hover:bg-gray-100 transition-colors relative"
        title="저장된 북마크"
      >
        <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
        </svg>
        {bookmarks.length > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-nexus-600 text-white text-[9px] rounded-full flex items-center justify-center">
            {bookmarks.length}
          </span>
        )}
      </button>

      {/* 메모 입력 팝업 */}
      {showAdd && (
        <div className="absolute right-0 top-full mt-1 z-30 bg-white border border-gray-200 rounded-lg shadow-lg p-3 w-64">
          <p className="text-xs font-medium text-gray-700 mb-2">북마크 메모</p>
          <input
            type="text"
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') addBookmark(); }}
            placeholder="메모 (선택사항)"
            className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded mb-2 focus:ring-1 focus:ring-nexus-500"
            autoFocus
          />
          <div className="flex justify-end gap-2">
            <button onClick={() => setShowAdd(false)} className="text-xs text-gray-500 hover:text-gray-700">취소</button>
            <button onClick={addBookmark} className="text-xs bg-nexus-600 text-white px-3 py-1 rounded hover:bg-nexus-700">저장</button>
          </div>
        </div>
      )}

      {/* 북마크 목록 드롭다운 */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-1 z-30 bg-white border border-gray-200 rounded-lg shadow-lg w-72 max-h-64 overflow-y-auto">
          {bookmarks.length === 0 ? (
            <p className="p-4 text-xs text-gray-500 text-center">저장된 북마크가 없습니다</p>
          ) : (
            bookmarks.map(bm => (
              <div
                key={bm.id}
                className="flex items-center gap-2 px-3 py-2.5 hover:bg-gray-50 border-b border-gray-50 last:border-0 cursor-pointer"
                onClick={() => { onLoadBookmark(bm.queryId); setIsOpen(false); }}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-800 truncate">{bm.label}</p>
                  {bm.memo && <p className="text-[10px] text-gray-500 truncate">{bm.memo}</p>}
                  <p className="text-[10px] text-gray-400">
                    {new Date(bm.createdAt).toLocaleDateString('ko-KR')}
                  </p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); removeBookmark(bm.id); }}
                  className="text-gray-300 hover:text-red-500 p-1"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
