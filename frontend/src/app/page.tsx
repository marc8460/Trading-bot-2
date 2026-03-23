'use client';

import { PnLCard } from '@/components/dashboard/PnLCard';
import { DrawdownGauge } from '@/components/dashboard/DrawdownGauge';
import { AccountCards } from '@/components/dashboard/AccountCards';
import { TradeLog } from '@/components/dashboard/TradeLog';
import { StrategyStatus } from '@/components/dashboard/StrategyStatus';
import { SystemHealth } from '@/components/dashboard/SystemHealth';
import { ControlPanel } from '@/components/controls/ControlPanel';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* ── Top metrics row ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <PnLCard
          label="Total P/L"
          value={4128.50}
          change={3.2}
          period="all time"
        />
        <PnLCard
          label="Today's P/L"
          value={312.00}
          change={0.6}
          period="today"
        />
        <PnLCard
          label="Active Trades"
          value={7}
          isCount
        />
        <SystemHealth status="running" uptime="3d 14h 22m" />
      </div>

      {/* ── Charts & Drawdown row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 glass-card p-6">
          <h3 className="text-sm font-medium text-muted mb-4">Equity Curve</h3>
          <div className="h-64 flex items-center justify-center text-surface-400">
            <p className="text-sm">Chart renders when connected to backend</p>
          </div>
        </div>
        <DrawdownGauge
          dailyDrawdown={1.2}
          dailyLimit={5.0}
          totalDrawdown={3.8}
          totalLimit={10.0}
        />
      </div>

      {/* ── Account cards ── */}
      <AccountCards
        accounts={[
          { id: 'ftmo_main', name: 'FTMO #1', firm: 'FTMO', phase: 'Funded', pnl: 892, drawdown: 2.1, status: 'active' },
          { id: 'e8_eval', name: 'E8 #1', firm: 'E8', phase: 'Evaluation', pnl: 156, drawdown: 0.8, status: 'active' },
          { id: 'fn_funded', name: 'FN #1', firm: 'FundedNext', phase: 'Funded', pnl: -23, drawdown: 0.1, status: 'warning' },
        ]}
      />

      {/* ── Trade log & Controls row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <TradeLog
            trades={[
              { time: '14:02:31', symbol: 'EURUSD', direction: 'LONG', volume: 0.5, account: 'FTMO#1', status: 'filled' },
              { time: '14:02:31', symbol: 'EURUSD', direction: 'LONG', volume: 0.3, account: 'E8#1', status: 'filled' },
              { time: '14:02:32', symbol: 'XAUUSD', direction: 'SHORT', volume: 0.1, account: 'FTMO#1', status: 'filled' },
              { time: '14:01:15', symbol: 'EURUSD', direction: 'LONG', volume: 0.5, account: 'FN#1', status: 'rejected' },
            ]}
          />
        </div>
        <div className="space-y-4">
          <ControlPanel />
          <StrategyStatus
            strategies={[
              { symbol: 'EURUSD', strategy: 'Trend Pullback', status: 'active', direction: 'up' },
              { symbol: 'XAUUSD', strategy: 'Trend Pullback', status: 'waiting', direction: null },
              { symbol: 'GBPUSD', strategy: '-', status: 'disabled', direction: null },
            ]}
          />
        </div>
      </div>
    </div>
  );
}
