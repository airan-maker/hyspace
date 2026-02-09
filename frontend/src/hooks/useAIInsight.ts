import { useState, useCallback, useRef } from 'react';
import { generateInsightStreamURL } from '../services/api';

interface InsightState {
  text: string;
  isLoading: boolean;
  error: string | null;
}

const cache = new Map<string, string>();

function hashKey(queryType: string, results: unknown): string {
  return `${queryType}:${JSON.stringify(results)}`.slice(0, 200);
}

export function useAIInsight() {
  const [state, setState] = useState<InsightState>({
    text: '',
    isLoading: false,
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);

  const generate = useCallback(async (queryType: string, results: unknown) => {
    // 캐시 확인
    const key = hashKey(queryType, results);
    const cached = cache.get(key);
    if (cached) {
      setState({ text: cached, isLoading: false, error: null });
      return;
    }

    // 이전 요청 취소
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ text: '', isLoading: true, error: null });

    try {
      const url = generateInsightStreamURL();
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_type: queryType, results }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('스트리밍을 사용할 수 없습니다.');

      const decoder = new TextDecoder();
      let accumulated = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const payload = line.slice(6).trim();
          if (payload === '[DONE]') break;

          try {
            const parsed = JSON.parse(payload);
            if (parsed.chunk) {
              accumulated += parsed.chunk;
              setState(prev => ({ ...prev, text: accumulated }));
            }
          } catch {
            // 파싱 실패 무시
          }
        }
      }

      // 캐시 저장
      cache.set(key, accumulated);
      setState({ text: accumulated, isLoading: false, error: null });
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === 'AbortError') return;
      const msg = e instanceof Error ? e.message : 'AI 분석 생성 실패';
      setState(prev => ({ ...prev, isLoading: false, error: msg }));
    }
  }, []);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    setState({ text: '', isLoading: false, error: null });
  }, []);

  return {
    insight: state.text,
    isLoading: state.isLoading,
    error: state.error,
    generate,
    clear,
  };
}
