/**
 * Real-time Data Hook
 *
 * WebSocket 기반 실시간 데이터 스트리밍 훅
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// ==================== Types ====================

export type StreamType =
  | 'yield_update'
  | 'equipment_status'
  | 'wip_movement'
  | 'alert'
  | 'metrics'
  | 'heartbeat';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

export interface StreamMessage {
  message_id: string;
  stream_type: StreamType;
  timestamp: string;
  data: Record<string, unknown>;
  priority: number;
}

export interface YieldUpdate {
  current_yield: number;
  target_yield: number;
  delta: number;
  trend: 'up' | 'down';
  process_step: string;
  lot_id: string;
  wafer_count: number;
}

export interface EquipmentStatus {
  equipment_id: string;
  status: 'RUNNING' | 'IDLE' | 'MAINTENANCE' | 'DOWN';
  previous_status: string;
  oee: number;
  temperature: number;
  utilization: number;
  wip_in_queue: number;
  estimated_completion: string;
}

export interface WIPMovement {
  lot_id: string;
  wafer_count: number;
  from_step: string;
  to_step: string;
  from_equipment: string;
  to_equipment: string;
  priority: 'NORMAL' | 'HIGH' | 'URGENT';
  progress: number;
  estimated_completion: string;
}

export interface AlertData {
  alert_id: string;
  title: string;
  message: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  category: string;
  requires_action: boolean;
  auto_escalate: boolean;
}

export interface FabMetrics {
  fab_metrics: {
    overall_yield: number;
    daily_output: number;
    active_lots: number;
    equipment_utilization: number;
  };
  equipment_summary: {
    total: number;
    running: number;
    idle: number;
    maintenance: number;
    down: number;
  };
  wip_summary: {
    total_lots: number;
    total_wafers: number;
    on_schedule: number;
    at_risk: number;
  };
  alerts_summary: {
    critical: number;
    error: number;
    warning: number;
    info: number;
  };
}

export interface RealtimeState {
  connectionStatus: ConnectionStatus;
  connectionId: string | null;
  lastYieldUpdate: YieldUpdate | null;
  equipmentStatuses: Map<string, EquipmentStatus>;
  recentWIPMovements: WIPMovement[];
  activeAlerts: AlertData[];
  metrics: FabMetrics | null;
  messageCount: number;
  lastMessageAt: Date | null;
}

export interface UseRealtimeOptions {
  autoConnect?: boolean;
  subscriptions?: StreamType[];
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onMessage?: (message: StreamMessage) => void;
  onAlert?: (alert: AlertData) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

// ==================== Hook ====================

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api';

export function useRealtime(options: UseRealtimeOptions = {}) {
  const {
    autoConnect = true,
    subscriptions = ['yield_update', 'equipment_status', 'wip_movement', 'alert', 'metrics'],
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onMessage,
    onAlert,
    onConnect,
    onDisconnect,
  } = options;

  const [state, setState] = useState<RealtimeState>({
    connectionStatus: 'disconnected',
    connectionId: null,
    lastYieldUpdate: null,
    equipmentStatuses: new Map(),
    recentWIPMovements: [],
    activeAlerts: [],
    metrics: null,
    messageCount: 0,
    lastMessageAt: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // WebSocket 연결
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setState(prev => ({ ...prev, connectionStatus: 'connecting' }));

    const subsParam = subscriptions.join(',');
    const ws = new WebSocket(`${WS_BASE_URL}/ws?subscriptions=${subsParam}`);

    ws.onopen = () => {
      setState(prev => ({ ...prev, connectionStatus: 'connected' }));
      reconnectAttemptsRef.current = 0;
      onConnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const message: StreamMessage = JSON.parse(event.data);
        handleMessage(message);
        onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      setState(prev => ({ ...prev, connectionStatus: 'disconnected', connectionId: null }));
      onDisconnect?.();

      // 자동 재연결
      if (reconnectAttemptsRef.current < maxReconnectAttempts) {
        setState(prev => ({ ...prev, connectionStatus: 'reconnecting' }));
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++;
          connect();
        }, reconnectInterval);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [subscriptions, reconnectInterval, maxReconnectAttempts, onConnect, onDisconnect, onMessage]);

  // 연결 해제
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    reconnectAttemptsRef.current = maxReconnectAttempts; // 재연결 방지
    wsRef.current?.close();
    wsRef.current = null;
  }, [maxReconnectAttempts]);

  // 메시지 처리
  const handleMessage = useCallback((message: StreamMessage) => {
    setState(prev => {
      const newState = {
        ...prev,
        messageCount: prev.messageCount + 1,
        lastMessageAt: new Date(),
      };

      switch (message.stream_type) {
        case 'heartbeat':
          if (message.data.connection_id) {
            newState.connectionId = message.data.connection_id as string;
          }
          break;

        case 'yield_update':
          newState.lastYieldUpdate = message.data as unknown as YieldUpdate;
          break;

        case 'equipment_status': {
          const equipStatus = message.data as unknown as EquipmentStatus;
          const newEquipMap = new Map(prev.equipmentStatuses);
          newEquipMap.set(equipStatus.equipment_id, equipStatus);
          newState.equipmentStatuses = newEquipMap;
          break;
        }

        case 'wip_movement': {
          const wipMovement = message.data as unknown as WIPMovement;
          newState.recentWIPMovements = [wipMovement, ...prev.recentWIPMovements].slice(0, 50);
          break;
        }

        case 'alert': {
          const alert = message.data as unknown as AlertData;
          newState.activeAlerts = [alert, ...prev.activeAlerts].slice(0, 100);
          onAlert?.(alert);
          break;
        }

        case 'metrics':
          newState.metrics = message.data as unknown as FabMetrics;
          break;
      }

      return newState;
    });
  }, [onAlert]);

  // 스트림 구독/해제
  const subscribe = useCallback((streams: StreamType[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        streams,
      }));
    }
  }, []);

  const unsubscribe = useCallback((streams: StreamType[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        streams,
      }));
    }
  }, []);

  // 메트릭 요청
  const requestMetrics = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'request_metrics',
      }));
    }
  }, []);

  // Ping
  const ping = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'ping',
      }));
    }
  }, []);

  // 알림 클리어
  const clearAlerts = useCallback(() => {
    setState(prev => ({ ...prev, activeAlerts: [] }));
  }, []);

  // 알림 제거
  const dismissAlert = useCallback((alertId: string) => {
    setState(prev => ({
      ...prev,
      activeAlerts: prev.activeAlerts.filter(a => a.alert_id !== alertId),
    }));
  }, []);

  // 자동 연결
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    // State
    ...state,

    // Connection
    connect,
    disconnect,
    isConnected: state.connectionStatus === 'connected',

    // Subscriptions
    subscribe,
    unsubscribe,

    // Actions
    requestMetrics,
    ping,
    clearAlerts,
    dismissAlert,

    // Computed
    criticalAlerts: state.activeAlerts.filter(a => a.severity === 'CRITICAL'),
    errorAlerts: state.activeAlerts.filter(a => a.severity === 'ERROR'),
    warningAlerts: state.activeAlerts.filter(a => a.severity === 'WARNING'),
    runningEquipment: Array.from(state.equipmentStatuses.values()).filter(e => e.status === 'RUNNING'),
    downEquipment: Array.from(state.equipmentStatuses.values()).filter(e => e.status === 'DOWN'),
  };
}

// ==================== Utility Hook ====================

/**
 * 특정 스트림만 구독하는 간단한 훅
 */
export function useRealtimeStream<T>(
  streamType: StreamType,
  initialValue: T | null = null
) {
  const [data, setData] = useState<T | null>(initialValue);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const { connectionStatus } = useRealtime({
    subscriptions: [streamType],
    onMessage: (message) => {
      if (message.stream_type === streamType) {
        setData(message.data as unknown as T);
        setLastUpdate(new Date());
      }
    },
  });

  return {
    data,
    lastUpdate,
    isConnected: connectionStatus === 'connected',
  };
}

/**
 * 실시간 수율 업데이트 훅
 */
export function useRealtimeYield() {
  return useRealtimeStream<YieldUpdate>('yield_update');
}

/**
 * 실시간 알림 훅
 */
export function useRealtimeAlerts(options: { maxAlerts?: number } = {}) {
  const { maxAlerts = 50 } = options;
  const [alerts, setAlerts] = useState<AlertData[]>([]);

  const { connectionStatus } = useRealtime({
    subscriptions: ['alert'],
    onAlert: (alert) => {
      setAlerts(prev => [alert, ...prev].slice(0, maxAlerts));
    },
  });

  const clearAlerts = useCallback(() => setAlerts([]), []);

  return {
    alerts,
    clearAlerts,
    isConnected: connectionStatus === 'connected',
    criticalCount: alerts.filter(a => a.severity === 'CRITICAL').length,
    errorCount: alerts.filter(a => a.severity === 'ERROR').length,
  };
}

export default useRealtime;
