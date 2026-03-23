interface Account {
  id: string;
  name: string;
  firm: string;
  phase: string;
  pnl: number;
  drawdown: number;
  status: 'active' | 'warning' | 'stopped';
}

interface AccountCardsProps {
  accounts: Account[];
}

export function AccountCards({ accounts }: AccountCardsProps) {
  const statusDot: Record<string, string> = {
    active: 'status-dot-active',
    warning: 'status-dot-warning',
    stopped: 'status-dot-inactive',
  };

  const firmColors: Record<string, string> = {
    FTMO: 'from-blue-500/20 to-blue-600/10 border-blue-500/30',
    E8: 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30',
    FundedNext: 'from-purple-500/20 to-purple-600/10 border-purple-500/30',
    The5ers: 'from-amber-500/20 to-amber-600/10 border-amber-500/30',
  };

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-medium text-muted mb-4">Accounts</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {accounts.map((account) => (
          <div
            key={account.id}
            className={`rounded-lg border bg-gradient-to-br p-4 transition-all duration-200
              hover:scale-[1.02] cursor-pointer
              ${firmColors[account.firm] || 'from-surface-200 to-surface-300 border-surface-400'}`}
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-200">{account.name}</h4>
              <div className={`status-dot ${statusDot[account.status]}`} />
            </div>

            <div className="flex items-center gap-2 mb-3">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface/50 text-muted font-medium">
                {account.firm}
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface/50 text-muted font-medium">
                {account.phase}
              </span>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-muted">P/L</span>
                <span className={`font-mono font-medium ${account.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                  ${account.pnl >= 0 ? '+' : ''}{account.pnl.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted">Drawdown</span>
                <span className="font-mono font-medium text-gray-300">{account.drawdown}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
