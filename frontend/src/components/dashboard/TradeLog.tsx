interface Trade {
  time: string;
  symbol: string;
  direction: 'LONG' | 'SHORT';
  volume: number;
  account: string;
  status: 'filled' | 'rejected' | 'pending';
}

interface TradeLogProps {
  trades: Trade[];
}

export function TradeLog({ trades }: TradeLogProps) {
  const statusIcon: Record<string, string> = {
    filled: '✓',
    rejected: '✗',
    pending: '◌',
  };

  const statusColor: Record<string, string> = {
    filled: 'text-success',
    rejected: 'text-danger',
    pending: 'text-warning',
  };

  const directionColor: Record<string, string> = {
    LONG: 'text-success bg-success/10',
    SHORT: 'text-danger bg-danger/10',
  };

  return (
    <div className="glass-card overflow-hidden">
      <div className="p-4 border-b border-surface-300/30 flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted">Live Trade Log</h3>
        <span className="text-[10px] px-2 py-1 rounded-full bg-accent/10 text-accent font-medium">
          LIVE
        </span>
      </div>

      <div className="max-h-64 overflow-y-auto">
        {trades.map((trade, i) => (
          <div key={i} className="trade-row">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono text-muted w-16">{trade.time}</span>
              <span className="text-xs font-semibold text-gray-200 w-16">{trade.symbol}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${directionColor[trade.direction]}`}>
                {trade.direction}
              </span>
              <span className="text-xs font-mono text-muted">{trade.volume}L</span>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-muted">{trade.account}</span>
              <span className={`text-sm font-bold ${statusColor[trade.status]}`}>
                {statusIcon[trade.status]}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
