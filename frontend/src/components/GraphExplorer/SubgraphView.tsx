import { useMemo, useState } from 'react';
import NetworkGraph from './NetworkGraph';
import { PRESET_FOCAL_NODES } from './constants';
import type { GraphNode, GraphVisualizationData } from '../../types/graph';

interface SubgraphViewProps {
  vizData: GraphVisualizationData;
  queryId: string;
  onNodeClick?: (node: GraphNode) => void;
}

export default function SubgraphView({ vizData, queryId, onNodeClick }: SubgraphViewProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);

  // 포컬 노드 기준 1-hop 서브그래프 추출
  const subgraph = useMemo(() => {
    const focalKeywords = PRESET_FOCAL_NODES[queryId] || [];
    if (focalKeywords.length === 0) return null;

    // 포컬 노드 찾기
    const focalIds = new Set<number>();
    for (const node of vizData.nodes) {
      if (focalKeywords.some(kw => node.name.toLowerCase().includes(kw.toLowerCase()))) {
        focalIds.add(node.id);
      }
    }
    if (focalIds.size === 0) return null;

    // 1-hop 이웃 + 관련 링크
    const neighborIds = new Set<number>(focalIds);
    const relevantLinks = vizData.links.filter((link) => {
      const src = typeof link.source === 'object' ? (link.source as any).id : link.source;
      const tgt = typeof link.target === 'object' ? (link.target as any).id : link.target;
      if (focalIds.has(src) || focalIds.has(tgt)) {
        neighborIds.add(src);
        neighborIds.add(tgt);
        return true;
      }
      return false;
    });

    const relevantNodes = vizData.nodes.filter(n => neighborIds.has(n.id));

    if (relevantNodes.length < 2) return null;

    return { nodes: relevantNodes, links: relevantLinks };
  }, [vizData, queryId]);

  if (!subgraph) return null;

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNodeId(prev => prev === node.id ? null : node.id);
    onNodeClick?.(node);
  };

  return (
    <div className="card mt-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-700">관계 서브그래프</h3>
        <span className="text-xs text-gray-400">
          {subgraph.nodes.length} 노드 · {subgraph.links.length} 관계
        </span>
      </div>
      <p className="text-xs text-gray-500 mb-3">
        질의 결과와 관련된 노드의 1-hop 이웃 관계를 시각화합니다. 노드를 클릭하면 연결 구조를 확인할 수 있습니다.
      </p>
      <div className="border border-gray-100 rounded-lg overflow-hidden bg-gray-50/50">
        <NetworkGraph
          data={subgraph}
          height={350}
          selectedNodeId={selectedNodeId}
          onNodeClick={handleNodeClick}
          onBackgroundClick={() => setSelectedNodeId(null)}
        />
      </div>
    </div>
  );
}
