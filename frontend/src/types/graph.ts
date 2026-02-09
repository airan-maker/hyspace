import type { GraphNode, GraphLink, GraphVisualizationData } from '../services/api';

export type { GraphNode, GraphLink, GraphVisualizationData };

/** force-graph 라이브러리가 런타임에 x,y 좌표를 추가한 노드 */
export interface GraphNodeWithPosition extends GraphNode {
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

/** force-graph 라이브러리용 데이터 포맷 */
export interface ForceGraphData {
  nodes: GraphNodeWithPosition[];
  links: GraphLink[];
}

/** 결과 뷰 / 그래프 뷰 전환 */
export type GraphViewMode = 'results' | 'graph' | 'map';

/** 노드 선택 시 이웃 정보 */
export interface NodeSelection {
  node: GraphNode | null;
  neighbors: Set<number>;
  links: Set<string>;
}
