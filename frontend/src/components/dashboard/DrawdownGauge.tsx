interface DrawdownGaugeProps {
  dailyDrawdown: number;
  dailyLimit: number;
  totalDrawdown: number;
  totalLimit: number;
}

export function DrawdownGauge({ dailyDrawdown, dailyLimit, totalDrawdown, totalLimit }: DrawdownGaugeProps) {
  const dailyPct = (dailyDrawdown / dailyLimit) * 100;
  const totalPct = (totalDrawdown / totalLimit) * 100;

  const getColor = (pct: number) => {
    if (pct < 50) return 'bg-success';
    if (pct < 75) return 'bg-warning';
    return 'bg-danger';
  };

  const getGlow = (pct: number) => {
    if (pct < 50) return '';
    if (pct < 75) return 'shadow-[0_0_8px_rgba(245,158,11,0.4)]';
    return 'shadow-[0_0_8px_rgba(239,68,68,0.4)]';
  };

  return (
    <div className="glass-card p-6 space-y-6">
      <h3 className="text-sm font-medium text-muted">Drawdown Status</h3>

      {/* Daily Drawdown */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted">Daily Drawdown</span>
          <span className="font-mono font-medium text-gray-200">
            {dailyDrawdown.toFixed(1)}% / {dailyLimit}%
          </span>
        </div>
        <div className="gauge-track">
          <div
            className={`gauge-fill ${getColor(dailyPct)} ${getGlow(dailyPct)}`}
            style={{ width: `${Math.min(dailyPct, 100)}%` }}
          />
        </div>
      </div>

      {/* Total Drawdown */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted">Total Drawdown</span>
          <span className="font-mono font-medium text-gray-200">
            {totalDrawdown.toFixed(1)}% / {totalLimit}%
          </span>
        </div>
        <div className="gauge-track">
          <div
            className={`gauge-fill ${getColor(totalPct)} ${getGlow(totalPct)}`}
            style={{ width: `${Math.min(totalPct, 100)}%` }}
          />
        </div>
      </div>

      {/* Remaining buffer */}
      <div className="pt-2 border-t border-surface-300/30">
        <div className="flex justify-between text-xs">
          <span className="text-muted">Daily Buffer</span>
          <span className="text-success font-mono">{(dailyLimit - dailyDrawdown).toFixed(1)}%</span>
        </div>
        <div className="flex justify-between text-xs mt-1">
          <span className="text-muted">Total Buffer</span>
          <span className="text-success font-mono">{(totalLimit - totalDrawdown).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}
