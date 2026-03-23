/**
 * PropOS — TypeScript type definitions
 * Mirrors backend Pydantic models for type-safe frontend usage.
 */

// ─── System ──────────────────────────────────

export type SystemStatus = 'starting' | 'running' | 'paused' | 'stopping' | 'stopped' | 'error' | 'kill_switch';

export interface SystemState {
  status: SystemStatus;
  started_at: string | null;
  last_heartbeat: string | null;
  kill_switch: {
    active: boolean;
    reason: string;
  };
  strategy: {
    active: string;
    last_signal: string | null;
    signals_today: number;
  };
  execution: {
    trades_today: number;
    open_positions: number;
  };
  accounts: Record<string, AccountState>;
}

// ─── Accounts ────────────────────────────────

export interface AccountState {
  connected: boolean;
  daily_pnl: number;
  total_pnl: number;
  daily_drawdown_pct: number;
  total_drawdown_pct: number;
  open_positions: number;
  trades_today: number;
  is_auto_stopped: boolean;
}

export interface AccountConfig {
  id: string;
  name: string;
  firm: string;
  phase: string;
  group: string;
  balance: number;
  enabled: boolean;
  risk_multiplier: number;
  symbols_allowed: string[];
}

// ─── Trades ──────────────────────────────────

export interface TradeRecord {
  id: string;
  signal_id: string;
  account_id: string;
  symbol: string;
  direction: 'long' | 'short';
  volume: number;
  open_price: number;
  close_price: number | null;
  stop_loss: number;
  take_profit: number;
  mt5_ticket: number | null;
  status: string;
  realized_pnl: number;
  close_reason: string;
  strategy: string;
  opened_at: string;
  closed_at: string | null;
}

// ─── Signals ─────────────────────────────────

export interface TradeSignal {
  id: string;
  symbol: string;
  direction: 'long' | 'short' | 'no_trade';
  strategy: string;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  confidence: number;
  timestamp: string;
}

// ─── Compliance ──────────────────────────────

export interface FirmProfile {
  name: string;
  slug: string;
  max_daily_drawdown_pct: number;
  max_total_drawdown_pct: number;
  max_positions: number;
}

// ─── WebSocket ───────────────────────────────

export interface WSMessage {
  type: 'state_update' | 'trade_update' | 'alert';
  data: unknown;
}
