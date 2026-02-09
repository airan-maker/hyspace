import { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { LABEL_COLORS, RELATIONSHIP_STYLES } from './constants';
import type { GraphNode, GraphVisualizationData } from '../../types/graph';

interface NetworkGraphProps {
  data: GraphVisualizationData;
  height?: number;
  selectedNodeId: number | null;
  onNodeClick: (node: GraphNode) => void;
  onBackgroundClick?: () => void;
  dagMode?: 'lr' | 'td' | null;
  className?: string;
  affectedNodeIds?: number[];
  darkMode?: boolean;
}

export default function NetworkGraph({
  data,
  height = 500,
  selectedNodeId,
  onNodeClick,
  onBackgroundClick,
  dagMode = null,
  className = '',
  affectedNodeIds = [],
  darkMode = true,
}: NetworkGraphProps) {
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(800);
  const [hoveredNode, setHoveredNode] = useState<any>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // Responsive width
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      const { width } = entries[0].contentRect;
      if (width > 0) setContainerWidth(width);
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Neighbor calculation
  const { neighborIds, linkKeys } = useMemo(() => {
    if (selectedNodeId === null) return { neighborIds: new Set<number>(), linkKeys: new Set<string>() };
    const nIds = new Set<number>();
    const lKeys = new Set<string>();
    for (const link of data.links) {
      const src = typeof link.source === 'object' ? (link.source as any).id : link.source;
      const tgt = typeof link.target === 'object' ? (link.target as any).id : link.target;
      if (src === selectedNodeId || tgt === selectedNodeId) {
        nIds.add(src);
        nIds.add(tgt);
        lKeys.add(`${src}-${tgt}`);
      }
    }
    return { neighborIds: nIds, linkKeys: lKeys };
  }, [selectedNodeId, data.links]);

  // Force tuning
  useEffect(() => {
    if (!fgRef.current) return;
    const fg = fgRef.current;
    fg.d3Force('charge')?.strength(-150);
    fg.d3Force('link')?.distance(70);
    if (!dagMode) {
      fg.d3Force('center')?.strength(0.05);
    }
  }, [data, dagMode]);

  const graphData = useMemo(() => ({
    nodes: data.nodes.map(n => ({ ...n })),
    links: data.links.map(l => ({ ...l })),
  }), [data]);

  const affectedSet = useMemo(() => new Set(affectedNodeIds), [affectedNodeIds]);

  // Color palette
  const labelText = darkMode ? '#e5e7eb' : '#374151';
  const dimmedText = darkMode ? '#6b7280' : '#d1d5db';

  // Node renderer
  const paintNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label || '';
    const name = node.name || '';
    const color = LABEL_COLORS[label] || '#9ca3af';
    const isSelected = node.id === selectedNodeId;
    const isNeighbor = neighborIds.has(node.id);
    const isAffected = affectedSet.has(node.id);
    const hasSelection = selectedNodeId !== null;
    const nodeR = label === 'ProcessStep' && dagMode ? 8 : 5;

    // Outer glow for selected/neighbor nodes
    if (darkMode && (isSelected || isNeighbor) && hasSelection) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, nodeR + 6, 0, 2 * Math.PI);
      const gradient = ctx.createRadialGradient(node.x, node.y, nodeR, node.x, node.y, nodeR + 8);
      gradient.addColorStop(0, `${color}40`);
      gradient.addColorStop(1, `${color}00`);
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    // Node shape
    ctx.beginPath();
    if (label === 'ProcessStep' && dagMode) {
      const w = 12, h = 8;
      ctx.roundRect(node.x - w, node.y - h, w * 2, h * 2, 3);
    } else {
      ctx.arc(node.x, node.y, nodeR, 0, 2 * Math.PI);
    }
    ctx.fillStyle = (hasSelection && !isSelected && !isNeighbor)
      ? `${color}30`
      : color;
    ctx.fill();

    // Selection highlight
    if (isSelected) {
      ctx.strokeStyle = darkMode ? '#ffffff' : '#ffffff';
      ctx.lineWidth = 2.5 / globalScale;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(node.x, node.y, nodeR + 3, 0, 2 * Math.PI);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5 / globalScale;
      ctx.stroke();
    }

    // What-if affected node highlight
    if (isAffected && !isSelected) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, nodeR + 4, 0, 2 * Math.PI);
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2 / globalScale;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(node.x, node.y, nodeR + 7, 0, 2 * Math.PI);
      ctx.strokeStyle = 'rgba(239, 68, 68, 0.3)';
      ctx.lineWidth = 3 / globalScale;
      ctx.stroke();
    }

    // Name label
    if (globalScale > 0.6) {
      const fontSize = Math.min(12 / globalScale, 4);
      ctx.font = `${fontSize}px Inter, -apple-system, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = (hasSelection && !isSelected && !isNeighbor) ? dimmedText : labelText;
      ctx.fillText(name, node.x, node.y + nodeR + 2);
    }
  }, [selectedNodeId, neighborIds, dagMode, affectedSet, darkMode, labelText, dimmedText]);

  // Link renderer
  const paintLink = useCallback((link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const src = link.source;
    const tgt = link.target;
    if (!src || !tgt || src.x == null || tgt.x == null) return;

    const srcId = typeof src === 'object' ? src.id : src;
    const tgtId = typeof tgt === 'object' ? tgt.id : tgt;
    const key = `${srcId}-${tgtId}`;
    const isHighlighted = linkKeys.has(key);
    const hasSelection = selectedNodeId !== null;
    const relStyle = RELATIONSHIP_STYLES[link.type] || { color: '#9ca3af' };

    const opacity = (hasSelection && !isHighlighted) ? 0.06 : darkMode ? 0.35 : 0.5;
    const lineColor = isHighlighted ? relStyle.color : darkMode ? `rgba(107,114,128,${opacity})` : `rgba(156,163,175,${opacity})`;
    const lineWidth = isHighlighted ? 1.2 / globalScale : 0.4 / globalScale;

    ctx.strokeStyle = lineColor;
    ctx.lineWidth = lineWidth;

    if (relStyle.dashed) {
      ctx.setLineDash([4 / globalScale, 3 / globalScale]);
    } else {
      ctx.setLineDash([]);
    }

    ctx.beginPath();
    ctx.moveTo(src.x, src.y);
    ctx.lineTo(tgt.x, tgt.y);
    ctx.stroke();
    ctx.setLineDash([]);

    // Arrow
    const arrowLen = 4 / globalScale;
    const dx = tgt.x - src.x;
    const dy = tgt.y - src.y;
    const angle = Math.atan2(dy, dx);
    const endX = tgt.x - Math.cos(angle) * 6;
    const endY = tgt.y - Math.sin(angle) * 6;

    ctx.fillStyle = lineColor;
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo(endX - arrowLen * Math.cos(angle - Math.PI / 6), endY - arrowLen * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(endX - arrowLen * Math.cos(angle + Math.PI / 6), endY - arrowLen * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();

    // Relationship label on highlight
    if (isHighlighted && globalScale > 1.0) {
      const midX = (src.x + tgt.x) / 2;
      const midY = (src.y + tgt.y) / 2;
      const fontSize = Math.min(9 / globalScale, 3.5);
      ctx.font = `${fontSize}px Inter, -apple-system, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = relStyle.color;
      ctx.fillText(link.type, midX, midY - 3 / globalScale);
    }
  }, [selectedNodeId, linkKeys, darkMode]);

  const paintNodePointerArea = useCallback((node: any, color: string, ctx: CanvasRenderingContext2D) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI);
    ctx.fill();
  }, []);

  const handleNodeHover = useCallback((node: any) => {
    setHoveredNode(node || null);
    if (node && containerRef.current && fgRef.current) {
      const coords = fgRef.current.graph2ScreenCoords(node.x, node.y);
      setTooltipPos({ x: coords.x, y: coords.y });
    }
  }, []);

  return (
    <div ref={containerRef} className={`relative ${className}`} style={{ height }}>
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        width={containerWidth}
        height={height}
        backgroundColor="transparent"
        nodeCanvasObject={paintNode}
        nodePointerAreaPaint={paintNodePointerArea}
        linkCanvasObject={paintLink}
        linkDirectionalArrowLength={0}
        onNodeClick={(node: any) => onNodeClick(node as GraphNode)}
        onNodeHover={handleNodeHover}
        onBackgroundClick={onBackgroundClick}
        dagMode={dagMode || undefined}
        dagLevelDistance={dagMode ? 100 : undefined}
        cooldownTicks={80}
        warmupTicks={30}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        minZoom={0.3}
        maxZoom={8}
      />

      {/* Hover tooltip */}
      {hoveredNode && (
        <div
          className={`absolute pointer-events-none z-10 rounded-lg shadow-lg px-3 py-2 text-xs max-w-[220px] ${
            darkMode
              ? 'glass-panel border border-gray-700 text-gray-200'
              : 'bg-white border border-gray-200 text-gray-800'
          }`}
          style={{
            left: Math.min(tooltipPos.x + 12, containerWidth - 230),
            top: Math.max(tooltipPos.y - 10, 0),
          }}
        >
          <div className="flex items-center gap-1.5 mb-1">
            <span
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: LABEL_COLORS[hoveredNode.label] || '#9ca3af' }}
            />
            <span className={`text-[10px] ${darkMode ? 'text-gray-400' : 'text-gray-400'}`}>{hoveredNode.label}</span>
          </div>
          <div className={`font-medium ${darkMode ? 'text-gray-100' : 'text-gray-800'}`}>{hoveredNode.name}</div>
          {hoveredNode.properties && (
            <div className="mt-1 space-y-0.5 text-[10px]">
              {Object.entries(hoveredNode.properties as Record<string, unknown>)
                .filter(([k]) => !['name', 'key'].includes(k))
                .slice(0, 4)
                .map(([k, v]) => (
                  <div key={k}>
                    <span className="text-gray-500">{k}:</span>{' '}
                    <span className={darkMode ? 'text-gray-300' : 'text-gray-600'}>{String(v)}</span>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
