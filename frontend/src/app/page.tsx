'use client';

import { useEffect, useState } from 'react';
import { PnLCard } from '@/components/dashboard/PnLCard';
import { DrawdownGauge } from '@/components/dashboard/DrawdownGauge';
import { AccountCards } from '@/components/dashboard/AccountCards';
import { TradeLog } from '@/components/dashboard/TradeLog';
import { StrategyStatus } from '@/components/dashboard/StrategyStatus';
import { SystemHealth } from '@/components/dashboard/SystemHealth';
import { ControlPanel } from '@/components/controls/ControlPanel';

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    // Poll the dashboard endpoint every 3 seconds
    const fetchData = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/dashboard/overview');
        if (res.ok) {
          const json = await res.json();
          setData(json.data);
        }
      } catch (e) {
        console.error("Failed to fetch dashboard data", e);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  // Compute aggregated stats
  const totalPnL = data ? Object.values(data.accounts || {}).reduce((acc: number, a: any) => acc + (a.total_pnl || 0), 0) : 0;
  const todayPnL = data ? Object.values(data.accounts || {}).reduce((acc: number, a: any) => acc + (a.daily_pnl || 0), 0) : 0;
  const activeTrades = data ? data.execution?.open_positions : 0;
  
  // Transform accounts dict to array
  const accounts = data && data.accounts ? Object.entries(data.accounts).map(([id, a]: [string, any]) => ({
    id,
    name: id,
    firm: 'Unknown', // Typically matched to config
    phase: 'Live',
    pnl: a.daily_pnl || 0,
    drawdown: a.daily_drawdown_pct || 0,
    status: (a.is_auto_stopped ? 'warning' : (a.connected ? 'active' : 'stopped')) as "warning" | "active" | "stopped"
  })) : [];
  
  // Highest drawdown for the gauge
  const highestDailyDrawdown = accounts.length > 0 ? Math.max(...accounts.map(a => a.drawdown)) : 0;
  
  // Transform strategy status
  const strategyInfo = data?.strategy ? [
    { 
      symbol: 'Global', 
      strategy: data.strategy.active || 'None', 
      status: 'active', 
      direction: data.strategy.signals_today > 0 ? 'up' : null 
    }
  ] : [];

  return (
    <div className="space-y-6">
      {/* ── Top metrics row ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <PnLCard
          label="Total P/L"
          value={totalPnL}
          change={0}
          period="all time"
        />
        <PnLCard
          label="Today's P/L"
          value={todayPnL}
          change={0}
          period="today"
        />
        <PnLCard
          label="Active Trades"
          value={activeTrades || 0}
          isCount
        />
        <SystemHealth status={data?.status || 'stopped'} uptime="Live" />
      </div>

      {/* ── Charts & Drawdown row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 glass-card p-6">
          <h3 className="text-sm font-medium text-muted mb-4">System Status</h3>
          <div className="h-64 flex flex-col items-center justify-center text-surface-400">
            <p className="text-xl font-bold mb-2">PropOS Engine: {data?.status?.toUpperCase() || 'OFFLINE'}</p>
            {data?.kill_switch?.active && (
              <p className="text-red-500 font-bold">KILL SWITCH ACTIVE: {data.kill_switch.reason}</p>
            )}
            <p className="text-sm mt-4">Signals Today: {data?.strategy?.signals_today || 0}</p>
            <p className="text-sm">Trades Executed Today: {data?.execution?.trades_today || 0}</p>
          </div>
        </div>
        <DrawdownGauge
          dailyDrawdown={highestDailyDrawdown}
          dailyLimit={5.0} // Dynamic limit should come from config, use default for MVP UI
          totalDrawdown={0}
          totalLimit={10.0}
        />
      </div>

      {/* ── Account cards ── */}
      <AccountCards accounts={accounts} />

      {/* ── Trade log & Controls row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <TradeLog
            trades={[]} // In the future, this should fetch recent actions from /api/dashboard 
          />
        </div>
        <div className="space-y-4">
          <ControlPanel />
          <StrategyStatus strategies={strategyInfo as any} />
        </div>
      </div>
    </div>
  );
}
