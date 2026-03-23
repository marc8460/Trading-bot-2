interface PnLCardProps {
  label: string;
  value: number;
  change?: number;
  period?: string;
  isCount?: boolean;
}

export function PnLCard({ label, value, change, period, isCount }: PnLCardProps) {
  const isPositive = value >= 0;

  return (
    <div className="metric-card">
      <span className="metric-label">{label}</span>
      <span className={`metric-value ${isCount ? 'text-white' : isPositive ? 'metric-positive' : 'metric-negative'}`}>
        {isCount ? value : `$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
        {!isCount && (
          <span className="text-sm ml-1">{isPositive ? '↑' : '↓'}</span>
        )}
      </span>
      {change !== undefined && (
        <span className={`text-xs ${isPositive ? 'text-success' : 'text-danger'}`}>
          {isPositive ? '+' : ''}{change}% {period}
        </span>
      )}
    </div>
  );
}
