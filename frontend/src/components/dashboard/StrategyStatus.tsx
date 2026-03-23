interface Strategy {
  symbol: string;
  strategy: string;
  status: 'active' | 'waiting' | 'disabled';
  direction: 'up' | 'down' | null;
}

interface StrategyStatusProps {
  strategies: Strategy[];
}

export function StrategyStatus({ strategies }: StrategyStatusProps) {
  const statusLabel: Record<string, { text: string; color: string }> = {
    active: { text: 'Active', color: 'text-success' },
    waiting: { text: 'Waiting', color: 'text-warning' },
    disabled: { text: 'Disabled', color: 'text-surface-400' },
  };

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-medium text-muted mb-3">Strategy Status</h3>
      <div className="space-y-3">
        {strategies.map((s) => (
          <div key={s.symbol} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-gray-200">{s.symbol}</span>
              <span className="text-xs text-muted">{s.strategy}</span>
            </div>
            <div className="flex items-center gap-2">
              {s.direction && (
                <span className={`text-sm ${s.direction === 'up' ? 'text-success' : 'text-danger'}`}>
                  {s.direction === 'up' ? '▲' : '▼'}
                </span>
              )}
              <span className={`text-xs font-medium ${statusLabel[s.status].color}`}>
                {statusLabel[s.status].text}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
