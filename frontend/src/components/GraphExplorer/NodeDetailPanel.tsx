import { useMemo } from 'react';
import { LABEL_COLORS } from './constants';
import type { GraphNode, GraphLink } from '../../types/graph';

interface NodeDetailPanelProps {
  node: GraphNode;
  links: GraphLink[];
  allNodes: GraphNode[];
  onClose: () => void;
  onNodeClick: (node: GraphNode) => void;
}

export default function NodeDetailPanel({ node, links, allNodes, onClose, onNodeClick }: NodeDetailPanelProps) {
  const color = LABEL_COLORS[node.label] || '#9ca3af';

  const connections = useMemo(() => {
    const nodeMap = new Map(allNodes.map(n => [n.id, n]));
    const outgoing: { type: string; node: GraphNode }[] = [];
    const incoming: { type: string; node: GraphNode }[] = [];

    for (const link of links) {
      const srcId = typeof link.source === 'object' ? (link.source as any).id : link.source;
      const tgtId = typeof link.target === 'object' ? (link.target as any).id : link.target;

      if (srcId === node.id) {
        const target = nodeMap.get(tgtId);
        if (target) outgoing.push({ type: link.type, node: target });
      } else if (tgtId === node.id) {
        const source = nodeMap.get(srcId);
        if (source) incoming.push({ type: link.type, node: source });
      }
    }
    return { outgoing, incoming };
  }, [node.id, links, allNodes]);

  const properties = node.properties || {};
  const displayProps = Object.entries(properties).filter(
    ([k]) => !['name', 'key'].includes(k) && properties[k] != null
  );

  return (
    <div className="absolute top-0 right-0 w-72 h-full bg-[#161B28] border-l border-gray-700 shadow-2xl overflow-y-auto z-20">
      {/* Header */}
      <div className="sticky top-0 bg-[#161B28] border-b border-gray-700 px-4 py-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
            <span className="text-[10px] text-gray-500 uppercase">{node.label}</span>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-lg leading-none">&times;</button>
        </div>
        <h3 className="text-sm font-semibold text-gray-100 mt-1">{node.name}</h3>
      </div>

      {/* Properties */}
      {displayProps.length > 0 && (
        <div className="px-4 py-3 border-b border-gray-700/50">
          <h4 className="text-[10px] font-semibold text-gray-500 uppercase mb-2">Properties</h4>
          <div className="space-y-1.5">
            {displayProps.map(([k, v]) => (
              <div key={k} className="flex items-start justify-between gap-2">
                <span className="text-[11px] text-gray-500 flex-shrink-0">{k}</span>
                <span className="text-[11px] text-gray-300 text-right break-all">
                  {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Outgoing */}
      {connections.outgoing.length > 0 && (
        <div className="px-4 py-3 border-b border-gray-700/50">
          <h4 className="text-[10px] font-semibold text-gray-500 uppercase mb-2">
            Outgoing ({connections.outgoing.length})
          </h4>
          <div className="space-y-1">
            {connections.outgoing.map((conn, i) => (
              <button
                key={i}
                onClick={() => onNodeClick(conn.node)}
                className="flex items-center gap-1.5 w-full text-left hover:bg-gray-800/50 rounded px-1.5 py-1 -mx-1.5 transition-colors"
              >
                <span className="text-[9px] text-gray-500 font-mono flex-shrink-0 w-28 truncate">{conn.type} &rarr;</span>
                <span
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ backgroundColor: LABEL_COLORS[conn.node.label] || '#9ca3af' }}
                />
                <span className="text-[11px] text-gray-300 truncate">{conn.node.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Incoming */}
      {connections.incoming.length > 0 && (
        <div className="px-4 py-3">
          <h4 className="text-[10px] font-semibold text-gray-500 uppercase mb-2">
            Incoming ({connections.incoming.length})
          </h4>
          <div className="space-y-1">
            {connections.incoming.map((conn, i) => (
              <button
                key={i}
                onClick={() => onNodeClick(conn.node)}
                className="flex items-center gap-1.5 w-full text-left hover:bg-gray-800/50 rounded px-1.5 py-1 -mx-1.5 transition-colors"
              >
                <span
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ backgroundColor: LABEL_COLORS[conn.node.label] || '#9ca3af' }}
                />
                <span className="text-[11px] text-gray-300 truncate">{conn.node.name}</span>
                <span className="text-[9px] text-gray-500 font-mono flex-shrink-0">&rarr; {conn.type}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
