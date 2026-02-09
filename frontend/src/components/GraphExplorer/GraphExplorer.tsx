/**
 * GraphExplorer — Full-screen network graph dashboard
 * Redesigned with dark theme, ranking sidebar, and immersive graph canvas.
 */
import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useGraphExplorer } from '../../hooks/useGraphExplorer';
import { useAIInsight } from '../../hooks/useAIInsight';
import { useWhatIf } from '../../hooks/useWhatIf';
import NetworkGraph from './NetworkGraph';
import NodeDetailPanel from './NodeDetailPanel';
import { ResultPanel } from './ResultRenderers';
import { LABEL_COLORS } from './constants';
import { SUGGESTED_EXPLORATIONS } from './constants';
import { searchGraphNodes, type SearchResultNode } from '../../services/api';
import type { GraphNode } from '../../types/graph';

/* ── Types ────────────────────────────────────── */

interface RankedEntity {
  node: GraphNode;
  score: number;
  label: string;
  color: string;
}

type OverlayPanel = 'none' | 'results' | 'queries' | 'whatif' | 'insight';

/* ── Main Component ──────────────────────────── */

export default function GraphExplorer({ onBack }: { onBack?: () => void }) {
  const {
    status,
    vizData,
    queryResult,
    selectedQuery,
    isLoading,
    isMigrating,
    error,
    selectedNode,
    setSelectedNode,
    fetchStatus,
    runMigration,
    fetchVisualization,
    executePreset,
    executeCypher,
  } = useGraphExplorer();

  const { insight, isLoading: insightLoading, generate: generateInsight } = useAIInsight();
  const { presets: whatIfPresets, result: whatIfResult, isLoading: whatIfLoading, executePreset: runWhatIf, clear: clearWhatIf } = useWhatIf();

  // Local state
  const [affectedNodeIds, setAffectedNodeIds] = useState<number[]>([]);
  const [activePanel, setActivePanel] = useState<OverlayPanel>('none');
  const [entityTypeFilter, setEntityTypeFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResultNode[]>([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const [viewToggle, setViewToggle] = useState<'network' | 'heatmap'>('network');
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Load status + viz
  useEffect(() => { fetchStatus(); }, [fetchStatus]);
  useEffect(() => {
    if (status?.available && (status.total_nodes || 0) > 0 && !vizData) {
      fetchVisualization();
    }
  }, [status, vizData, fetchVisualization]);

  // What-if affected nodes sync
  useEffect(() => {
    if (whatIfResult) {
      setAffectedNodeIds(whatIfResult.affected_node_ids);
    }
  }, [whatIfResult]);

  // Close search dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setSearchOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      if (!searchQuery.trim()) { setSearchResults([]); setSearchOpen(false); return; }
      try {
        const res = await searchGraphNodes({ q: searchQuery, limit: 12 });
        setSearchResults(res.results);
        setSearchOpen(true);
      } catch { setSearchResults([]); }
    }, 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [searchQuery]);

  // Open results panel when query completes
  useEffect(() => {
    if (queryResult && selectedQuery) setActivePanel('results');
  }, [queryResult, selectedQuery]);

  /* ── Computed data ──────────────────────────── */

  const hasData = status?.available && (status.total_nodes || 0) > 0;

  // Entity ranking from viz data
  const rankedEntities: RankedEntity[] = useMemo(() => {
    if (!vizData) return [];
    const connectionCount = new Map<number, number>();
    for (const link of vizData.links) {
      const srcId = typeof link.source === 'object' ? (link.source as any).id : link.source;
      const tgtId = typeof link.target === 'object' ? (link.target as any).id : link.target;
      connectionCount.set(srcId, (connectionCount.get(srcId) || 0) + 1);
      connectionCount.set(tgtId, (connectionCount.get(tgtId) || 0) + 1);
    }
    return vizData.nodes
      .map(n => ({
        node: n,
        score: connectionCount.get(n.id) || 0,
        label: n.label,
        color: LABEL_COLORS[n.label] || '#9ca3af',
      }))
      .filter(e => entityTypeFilter === 'All' || e.label === entityTypeFilter)
      .sort((a, b) => b.score - a.score)
      .slice(0, 30);
  }, [vizData, entityTypeFilter]);

  // Available entity types
  const entityTypes = useMemo(() => {
    if (!vizData) return [];
    return [...new Set(vizData.nodes.map(n => n.label))].sort();
  }, [vizData]);

  // Graph summary
  const graphSummary = useMemo(() => {
    if (!status) return { nodes: 0, relationships: 0 };
    return { nodes: status.total_nodes || 0, relationships: status.total_relationships || 0 };
  }, [status]);

  /* ── Handlers ───────────────────────────────── */

  const handleGraphNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(prev => prev?.id === node.id ? null : node);
  }, [setSelectedNode]);

  const handleSearchSelect = useCallback((searchNode: SearchResultNode) => {
    if (vizData) {
      const graphNode = vizData.nodes.find(n => n.name === searchNode.name && n.label === searchNode.label);
      if (graphNode) setSelectedNode(graphNode);
    }
    setSearchOpen(false);
    setSearchQuery('');
  }, [vizData, setSelectedNode]);

  const handlePresetClick = useCallback((presetId: string) => {
    executePreset(presetId);
    setActivePanel('results');
  }, [executePreset]);

  const handleWhatIf = useCallback(async (presetId: string) => {
    const preset = whatIfPresets.find(p => p.id === presetId);
    if (!preset) return;
    await runWhatIf(preset, false);
  }, [whatIfPresets, runWhatIf]);

  const handleClearWhatIf = useCallback(() => {
    clearWhatIf();
    setAffectedNodeIds([]);
  }, [clearWhatIf]);

  const togglePanel = useCallback((panel: OverlayPanel) => {
    setActivePanel(prev => prev === panel ? 'none' : panel);
  }, []);

  /* ── Render ─────────────────────────────────── */

  return (
    <div className="graph-explorer h-screen flex flex-col overflow-hidden bg-[#0F111A] text-gray-200 font-[Inter,system-ui,sans-serif]">

      {/* ═══ Header ═══ */}
      <header className="h-16 border-b border-gray-800 bg-[#161B28] flex items-center justify-between px-6 shrink-0 z-20">
        <div className="flex items-center space-x-6">
          {/* Logo + back */}
          <button onClick={onBack} className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-teal-400 flex items-center justify-center font-bold text-sm text-white">
              SN
            </div>
            <span className="font-bold text-lg tracking-tight text-white group-hover:text-blue-400 transition-colors">
              Silicon Nexus
            </span>
          </button>

          <div className="h-8 w-px bg-gray-700 mx-2" />

          <div className="flex flex-col">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Explorer</span>
            <span className="text-sm font-medium text-gray-100">Supply Chain Network</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Query Presets */}
          <button
            onClick={() => togglePanel('queries')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md border transition-colors text-xs font-medium ${
              activePanel === 'queries'
                ? 'bg-blue-600/20 border-blue-500/50 text-blue-400'
                : 'bg-gray-800 border-transparent hover:border-gray-600 text-gray-300'
            }`}
          >
            <svg className="w-3.5 h-3.5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
            </svg>
            <span>Queries</span>
          </button>

          {/* What-If */}
          <button
            onClick={() => togglePanel('whatif')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md border transition-colors text-xs font-medium ${
              activePanel === 'whatif'
                ? 'bg-red-600/20 border-red-500/50 text-red-400'
                : 'bg-gray-800 border-transparent hover:border-gray-600 text-gray-300'
            }`}
          >
            <svg className="w-3.5 h-3.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>What-If</span>
          </button>

          {/* AI Insight */}
          <button
            onClick={() => togglePanel('insight')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md border transition-colors text-xs font-medium ${
              activePanel === 'insight'
                ? 'bg-purple-600/20 border-purple-500/50 text-purple-400'
                : 'bg-gray-800 border-transparent hover:border-gray-600 text-gray-300'
            }`}
          >
            <svg className="w-3.5 h-3.5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <span>AI Insight</span>
          </button>

          <div className="flex items-center space-x-2 pl-3 border-l border-gray-700">
            {/* Connection status */}
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${status?.available ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-xs text-gray-400">
                {status?.available ? 'Neo4j' : 'Disconnected'}
              </span>
            </div>

            {/* Migration button */}
            {status?.available && (
              <button
                onClick={runMigration}
                disabled={isMigrating}
                className="px-2 py-1 text-[10px] bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded text-gray-400 disabled:opacity-50"
              >
                {isMigrating ? 'Migrating...' : hasData ? 'Re-migrate' : 'Migrate'}
              </button>
            )}
          </div>
        </div>
      </header>

      {/* ═══ Filter Bar ═══ */}
      <div className="h-14 border-b border-gray-800 bg-[#0F111A] flex items-center px-6 shrink-0 space-x-6 z-10">
        {/* Search */}
        <div className="relative w-96" ref={searchRef}>
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            className="w-full pl-10 pr-4 py-1.5 bg-[#161B28] border border-gray-700 rounded-md text-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-500 text-gray-200"
            placeholder="Search entity, material or equipment..."
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => { if (searchResults.length > 0) setSearchOpen(true); }}
          />

          {/* Search dropdown */}
          {searchOpen && searchResults.length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-1 z-50 bg-[#161B28] border border-gray-700 rounded-lg shadow-2xl max-h-72 overflow-y-auto">
              {searchResults.map((node, i) => (
                <button
                  key={i}
                  onClick={() => handleSearchSelect(node)}
                  className="w-full text-left px-4 py-2.5 hover:bg-gray-800 transition-colors border-b border-gray-800 last:border-0"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: LABEL_COLORS[node.label] || '#9ca3af' }} />
                    <span className="text-sm font-medium text-gray-200">{node.name}</span>
                    <span className="text-[10px] text-gray-500">{node.label}</span>
                    <span className="ml-auto text-[10px] text-gray-500">{node.connection_count} conn.</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex-1" />

        {/* Graph Stats */}
        <div className="flex items-center space-x-6 text-sm">
          <div className="flex flex-col">
            <span className="text-[10px] text-gray-500 uppercase font-semibold mb-0.5">Nodes</span>
            <span className="text-base font-bold font-mono text-blue-400">{graphSummary.nodes}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-gray-500 uppercase font-semibold mb-0.5">Relationships</span>
            <span className="text-base font-bold font-mono text-teal-400">{graphSummary.relationships}</span>
          </div>

          {/* Entity Type Filter */}
          <div className="flex flex-col w-32">
            <span className="text-[10px] text-gray-500 uppercase font-semibold mb-0.5">Entity Type</span>
            <select
              value={entityTypeFilter}
              onChange={(e) => setEntityTypeFilter(e.target.value)}
              className="bg-transparent text-sm font-medium text-gray-200 cursor-pointer outline-none border-none"
            >
              <option value="All" className="bg-[#161B28]">All</option>
              {entityTypes.map(t => (
                <option key={t} value={t} className="bg-[#161B28]">{t}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* ═══ Main Area ═══ */}
      <main className="flex-1 flex overflow-hidden relative">

        {/* ─── Graph Canvas ─── */}
        <div className="flex-1 relative bg-gradient-to-b from-[#0F111A] to-[#0B0D14] overflow-hidden" id="graph-container">
          {/* Dot grid */}
          <div className="absolute inset-0 opacity-20 pointer-events-none dot-grid" />

          {/* View toggle */}
          <div className="absolute top-4 left-4 flex bg-[#161B28] rounded-lg p-1 shadow-lg border border-gray-700 z-10">
            <button
              onClick={() => setViewToggle('network')}
              className={`px-4 py-1.5 rounded text-xs font-medium transition-colors ${
                viewToggle === 'network' ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-500 hover:text-white'
              }`}
            >
              Network
            </button>
            <button
              onClick={() => setViewToggle('heatmap')}
              className={`px-4 py-1.5 rounded text-xs font-medium transition-colors ${
                viewToggle === 'heatmap' ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-500 hover:text-white'
              }`}
            >
              Heatmap
            </button>
          </div>

          {/* Zoom Controls */}
          <div className="absolute top-4 right-4 flex flex-col space-y-2 z-10">
            <button className="w-8 h-8 rounded-full bg-[#161B28] border border-gray-700 flex items-center justify-center shadow-lg hover:bg-gray-700 text-gray-400 hover:text-white transition-colors">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            </button>
            <button className="w-8 h-8 rounded-full bg-[#161B28] border border-gray-700 flex items-center justify-center shadow-lg hover:bg-gray-700 text-gray-400 hover:text-white transition-colors">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" /></svg>
            </button>
            <button className="w-8 h-8 rounded-full bg-[#161B28] border border-gray-700 flex items-center justify-center shadow-lg hover:bg-gray-700 text-gray-400 hover:text-white transition-colors mt-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
            </button>
          </div>

          {/* Graph or empty state */}
          {hasData && vizData ? (
            <div className="absolute inset-0 z-[1]">
              <NetworkGraph
                data={vizData}
                height={window.innerHeight - 160} // approximate: header + filter + timeline
                selectedNodeId={selectedNode?.id ?? null}
                onNodeClick={handleGraphNodeClick}
                onBackgroundClick={() => { setSelectedNode(null); }}
                dagMode={selectedQuery === 'process_flow' ? 'lr' : null}
                affectedNodeIds={affectedNodeIds}
                darkMode
              />
              {/* Node detail overlay */}
              {selectedNode && (
                <NodeDetailPanel
                  node={selectedNode}
                  links={vizData.links}
                  allNodes={vizData.nodes}
                  onClose={() => setSelectedNode(null)}
                  onNodeClick={handleGraphNodeClick}
                />
              )}
            </div>
          ) : (
            <div className="absolute inset-0 flex items-center justify-center z-[1]">
              <div className="text-center">
                {!status?.available ? (
                  <>
                    <div className="w-16 h-16 rounded-full bg-red-900/30 border border-red-800 flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <p className="text-gray-400 text-sm mb-1">Neo4j 미연결</p>
                    <p className="text-gray-600 text-xs">docker-compose up neo4j 실행 필요</p>
                  </>
                ) : !hasData ? (
                  <>
                    <div className="w-16 h-16 rounded-full bg-amber-900/30 border border-amber-800 flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                      </svg>
                    </div>
                    <p className="text-gray-400 text-sm mb-3">데이터가 없습니다</p>
                    <button
                      onClick={runMigration}
                      disabled={isMigrating}
                      className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
                    >
                      {isMigrating ? 'Migrating...' : '온톨로지 마이그레이션'}
                    </button>
                  </>
                ) : (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin w-6 h-6 border-2 border-gray-700 border-t-blue-400 rounded-full" />
                    <span className="text-gray-500 text-sm">그래프 로딩 중...</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ─── Left Overlay Panels ─── */}

          {/* Queries Panel */}
          {activePanel === 'queries' && (
            <div className="absolute top-4 left-4 w-80 max-h-[calc(100%-80px)] glass-panel rounded-lg border border-gray-700 shadow-2xl z-30 overflow-y-auto">
              <div className="p-4 border-b border-gray-700 flex items-center justify-between sticky top-0 glass-panel rounded-t-lg">
                <h3 className="text-sm font-semibold text-gray-100">Preset Queries</h3>
                <button onClick={() => setActivePanel('none')} className="text-gray-500 hover:text-gray-300">&times;</button>
              </div>
              <div className="p-3 space-y-4">
                {SUGGESTED_EXPLORATIONS.map((cat) => (
                  <div key={cat.category}>
                    <h4 className="text-[10px] font-semibold text-gray-500 uppercase mb-2 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: cat.color }} />
                      {cat.category}
                    </h4>
                    <div className="space-y-1">
                      {cat.queries.map((q) => (
                        <button
                          key={q.presetId}
                          onClick={() => handlePresetClick(q.presetId)}
                          disabled={isLoading}
                          className={`w-full text-left px-3 py-2 rounded-md text-xs transition-colors ${
                            selectedQuery === q.presetId
                              ? 'bg-blue-600/20 border border-blue-500/30 text-blue-300'
                              : 'hover:bg-gray-800 text-gray-300 border border-transparent'
                          } disabled:opacity-50`}
                        >
                          <div className="font-medium">{q.title}</div>
                          <div className="text-[10px] text-gray-500 mt-0.5">{q.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Cypher Input */}
                <div>
                  <h4 className="text-[10px] font-semibold text-gray-500 uppercase mb-2">Custom Cypher</h4>
                  <div className="flex gap-1.5">
                    <input
                      id="cypher-input"
                      className="flex-1 px-2 py-1.5 bg-[#111420] border border-gray-700 rounded text-xs text-gray-200 placeholder-gray-600 focus:ring-1 focus:ring-blue-500"
                      placeholder="MATCH (n) RETURN n LIMIT 10"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          const val = (e.target as HTMLInputElement).value;
                          if (val.trim()) executeCypher(val);
                        }
                      }}
                    />
                    <button
                      onClick={() => {
                        const el = document.getElementById('cypher-input') as HTMLInputElement;
                        if (el?.value.trim()) executeCypher(el.value);
                      }}
                      className="px-2 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
                    >
                      Run
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Results Panel */}
          {activePanel === 'results' && selectedQuery && (
            <div className="absolute top-4 left-4 w-96 max-h-[calc(100%-80px)] glass-panel rounded-lg border border-gray-700 shadow-2xl z-30 overflow-y-auto">
              <div className="p-4 border-b border-gray-700 flex items-center justify-between sticky top-0 glass-panel rounded-t-lg">
                <div>
                  <h3 className="text-sm font-semibold text-gray-100">Results</h3>
                  <span className="text-[10px] text-gray-500 font-mono">{selectedQuery}</span>
                </div>
                <button onClick={() => setActivePanel('none')} className="text-gray-500 hover:text-gray-300">&times;</button>
              </div>
              <div className="p-3">
                <ResultPanel
                  result={queryResult}
                  selectedQuery={selectedQuery}
                  isLoading={isLoading}
                  error={error}
                />
              </div>
            </div>
          )}

          {/* What-If Panel */}
          {activePanel === 'whatif' && (
            <div className="absolute top-4 left-4 w-80 max-h-[calc(100%-80px)] glass-panel rounded-lg border border-gray-700 shadow-2xl z-30 overflow-y-auto">
              <div className="p-4 border-b border-gray-700 flex items-center justify-between sticky top-0 glass-panel rounded-t-lg">
                <h3 className="text-sm font-semibold text-gray-100">What-If Scenarios</h3>
                <button onClick={() => setActivePanel('none')} className="text-gray-500 hover:text-gray-300">&times;</button>
              </div>
              <div className="p-3 space-y-3">
                <p className="text-xs text-gray-500">시나리오를 선택하면 영향 노드를 그래프에서 하이라이트합니다.</p>
                <div className="flex flex-wrap gap-1.5">
                  {whatIfPresets.map(p => (
                    <button
                      key={p.id}
                      onClick={() => handleWhatIf(p.id)}
                      disabled={whatIfLoading}
                      className="px-2.5 py-1.5 text-xs rounded-md border border-gray-700 hover:border-red-600/50 hover:bg-red-900/20 text-gray-300 transition-colors disabled:opacity-50"
                      title={p.description}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>

                {whatIfLoading && (
                  <div className="flex items-center gap-2 py-4 justify-center">
                    <div className="animate-spin w-4 h-4 border-2 border-red-800 border-t-red-400 rounded-full" />
                    <span className="text-xs text-gray-500">분석 중...</span>
                  </div>
                )}

                {whatIfResult && !whatIfLoading && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 p-2 bg-[#111420] rounded-lg">
                      <div className="text-center">
                        <div className="text-xl font-bold text-red-400">{whatIfResult.total_affected}</div>
                        <div className="text-[10px] text-gray-500">Affected</div>
                      </div>
                      {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(sev => {
                        const count = whatIfResult.affected_nodes.filter(n => n.severity === sev).length;
                        if (count === 0) return null;
                        const colors: Record<string, string> = { CRITICAL: '#dc2626', HIGH: '#ea580c', MEDIUM: '#ca8a04', LOW: '#65a30d' };
                        return (
                          <div key={sev} className="text-center">
                            <div className="text-sm font-semibold" style={{ color: colors[sev] }}>{count}</div>
                            <div className="text-[10px] text-gray-500">{sev}</div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {whatIfResult.affected_nodes.map(node => {
                        const sevColors: Record<string, string> = { CRITICAL: '#dc2626', HIGH: '#ea580c', MEDIUM: '#ca8a04', LOW: '#65a30d' };
                        return (
                          <div key={node.id} className="flex items-start gap-2 p-1.5 rounded hover:bg-gray-800/50 text-xs">
                            <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1" style={{ backgroundColor: sevColors[node.severity] || '#9ca3af' }} />
                            <div className="flex-1 min-w-0">
                              <span className="text-gray-200 font-medium">{node.name}</span>
                              <span className="text-gray-500 ml-1.5">{node.label}</span>
                              <p className="text-[10px] text-gray-500">{node.impact_reason}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <button
                      onClick={handleClearWhatIf}
                      className="text-xs text-gray-500 hover:text-red-400 transition-colors"
                    >
                      Clear
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AI Insight Panel */}
          {activePanel === 'insight' && (
            <div className="absolute top-4 left-4 w-96 max-h-[calc(100%-80px)] glass-panel rounded-lg border border-gray-700 shadow-2xl z-30 overflow-y-auto">
              <div className="p-4 border-b border-gray-700 flex items-center justify-between sticky top-0 glass-panel rounded-t-lg">
                <h3 className="text-sm font-semibold text-gray-100">AI Insight</h3>
                <div className="flex items-center gap-2">
                  {!!(selectedQuery && queryResult) && !insightLoading && (
                    <button
                      onClick={() => generateInsight(selectedQuery, queryResult)}
                      className="px-2 py-1 text-xs bg-purple-600 hover:bg-purple-700 text-white rounded transition-colors"
                    >
                      {insight ? 'Regenerate' : 'Generate'}
                    </button>
                  )}
                  <button onClick={() => setActivePanel('none')} className="text-gray-500 hover:text-gray-300">&times;</button>
                </div>
              </div>
              <div className="p-3">
                {insightLoading && !insight && (
                  <div className="space-y-2 animate-pulse">
                    <div className="h-3 bg-gray-700 rounded w-3/4" />
                    <div className="h-3 bg-gray-700 rounded w-full" />
                    <div className="h-3 bg-gray-700 rounded w-5/6" />
                    <div className="h-3 bg-gray-700 rounded w-2/3" />
                  </div>
                )}
                {insight && (
                  <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
                    {insight}
                    {insightLoading && <span className="inline-block w-2 h-4 bg-purple-500 animate-pulse ml-0.5" />}
                  </div>
                )}
                {!insight && !insightLoading && (
                  <p className="text-xs text-gray-500">
                    {selectedQuery && queryResult
                      ? '"Generate" 버튼을 클릭하여 AI 분석을 생성하세요.'
                      : '먼저 쿼리를 실행한 후 AI 분석을 생성할 수 있습니다.'}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* ─── Bottom Timeline Bar ─── */}
          <div className="absolute bottom-0 left-0 right-0 h-16 glass-panel border-t border-gray-800 flex items-center px-6 space-x-4 z-20">
            <div className="flex flex-col">
              <span className="text-[10px] uppercase font-bold text-gray-500">Entities</span>
              <span className="text-xl font-bold font-mono text-gray-200">{graphSummary.nodes}</span>
            </div>

            <div className="h-8 w-px bg-gray-700" />

            {/* Label legend inline */}
            <div className="flex-1 flex items-center gap-3 overflow-x-auto">
              {Object.entries(LABEL_COLORS).map(([label, color]) => {
                const count = vizData?.nodes.filter(n => n.label === label).length || 0;
                if (count === 0) return null;
                return (
                  <button
                    key={label}
                    onClick={() => setEntityTypeFilter(prev => prev === label ? 'All' : label)}
                    className={`flex items-center gap-1.5 shrink-0 px-2 py-1 rounded transition-colors ${
                      entityTypeFilter === label ? 'bg-gray-700' : 'hover:bg-gray-800/50'
                    }`}
                  >
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-[10px] text-gray-400">{label}</span>
                    <span className="text-[10px] text-gray-600 font-mono">{count}</span>
                  </button>
                );
              })}
            </div>

            <div className="h-8 w-px bg-gray-700" />

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex items-center gap-2">
                <div className="animate-spin w-4 h-4 border-2 border-gray-700 border-t-blue-400 rounded-full" />
                <span className="text-xs text-gray-500">Loading...</span>
              </div>
            )}
          </div>
        </div>

        {/* ─── Right Sidebar: Entity Ranking ─── */}
        <aside className="w-80 bg-[#161B28] border-l border-gray-800 flex flex-col z-20 shadow-xl">
          <div className="p-4 border-b border-gray-800 flex items-center justify-between shrink-0">
            <h2 className="text-sm font-semibold text-gray-100">Entity Ranking</h2>
            <select
              value={entityTypeFilter}
              onChange={(e) => setEntityTypeFilter(e.target.value)}
              className="text-xs bg-transparent text-gray-400 cursor-pointer outline-none border-none"
            >
              <option value="All" className="bg-[#161B28]">All Types</option>
              {entityTypes.map(t => (
                <option key={t} value={t} className="bg-[#161B28]">{t}</option>
              ))}
            </select>
          </div>

          {/* Column headers */}
          <div className="flex items-center px-4 py-2 text-[10px] font-semibold text-gray-500 uppercase border-b border-gray-800 bg-[#111420]">
            <span className="w-6">#</span>
            <span className="flex-1">Name</span>
            <span className="w-10 text-right">Conn.</span>
            <span className="w-14 text-right">Label</span>
          </div>

          {/* Scrollable list */}
          <div className="flex-1 overflow-y-auto">
            {rankedEntities.length === 0 ? (
              <div className="flex items-center justify-center py-12 text-gray-600 text-sm">
                {hasData ? 'No entities match filter' : 'No data available'}
              </div>
            ) : (
              <div className="divide-y divide-gray-800">
                {rankedEntities.map((entity, idx) => (
                  <button
                    key={entity.node.id}
                    onClick={() => handleGraphNodeClick(entity.node)}
                    className={`w-full flex items-center px-4 py-3 hover:bg-gray-800/50 cursor-pointer transition-colors group text-left ${
                      selectedNode?.id === entity.node.id ? 'bg-blue-900/20 border-l-2 border-l-blue-500' : ''
                    }`}
                  >
                    <span className="w-6 text-xs text-gray-500 font-mono">{idx + 1}</span>
                    <div className="flex-1 flex items-center space-x-2 min-w-0">
                      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: entity.color }} />
                      <span className="text-xs font-medium text-gray-300 group-hover:text-blue-400 truncate">
                        {entity.node.name}
                      </span>
                    </div>
                    <span className="w-10 text-right text-xs text-gray-500 font-mono">{entity.score}</span>
                    <span className="w-14 text-right">
                      <span
                        className="inline-block px-1.5 py-0.5 text-[9px] rounded-full font-medium text-white/80"
                        style={{ backgroundColor: `${entity.color}40`, color: entity.color }}
                      >
                        {entity.label.length > 8 ? entity.label.slice(0, 8) + '..' : entity.label}
                      </span>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-gray-800 flex items-center justify-between">
            <span className="text-[10px] text-gray-600">
              {rankedEntities.length} of {vizData?.nodes.length || 0} entities
            </span>
            <button
              onClick={() => setEntityTypeFilter('All')}
              className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
            >
              Show all
            </button>
          </div>
        </aside>
      </main>
    </div>
  );
}
