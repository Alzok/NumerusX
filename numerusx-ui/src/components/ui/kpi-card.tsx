import React from 'react';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface KpiCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    percentage: number;
    period: string; // e.g., "24h", "7d", "1m"
  };
  icon?: React.ReactNode;
  className?: string;
  isLoading?: boolean;
  trend?: 'up' | 'down' | 'neutral';
  formatter?: (value: number) => string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  change,
  icon,
  className,
  isLoading = false,
  trend,
  formatter,
}) => {
  // Détecter automatiquement la tendance depuis change si pas fournie
  const getTrend = () => {
    if (trend) return trend;
    if (change && change.value !== 0) {
      return change.value > 0 ? 'up' : 'down';
    }
    return 'neutral';
  };

  const currentTrend = getTrend();

  const getTrendIcon = () => {
    switch (currentTrend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <Minus className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTrendColor = () => {
    switch (currentTrend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-400';
    }
  };

  const formatValue = (val: string | number) => {
    if (typeof val === 'number' && formatter) {
      return formatter(val);
    }
    return val;
  };

  if (isLoading) {
    return (
      <div className={cn(
        "bg-card rounded-lg border p-6 shadow-sm",
        className
      )}>
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
            <div className="h-8 w-32 bg-gray-200 rounded animate-pulse" />
          </div>
          {icon && (
            <div className="h-8 w-8 bg-gray-200 rounded animate-pulse" />
          )}
        </div>
        {change && (
          <div className="mt-4 flex items-center space-x-2">
            <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={cn(
      "bg-card rounded-lg border p-6 shadow-sm hover:shadow-md transition-shadow",
      className
    )}>
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
            {title}
          </p>
          <p className="text-3xl font-bold tracking-tight">
            {formatValue(value)}
          </p>
        </div>
        {icon && (
          <div className="h-8 w-8 text-muted-foreground">
            {icon}
          </div>
        )}
      </div>
      
      {change && (
        <div className="mt-4 flex items-center space-x-2">
          {getTrendIcon()}
          <span className={cn("text-sm font-medium", getTrendColor())}>
            {change.value > 0 ? '+' : ''}
            {formatter ? formatter(change.value) : change.value}
            {' '}
            ({change.percentage > 0 ? '+' : ''}{change.percentage.toFixed(1)}%)
          </span>
          <span className="text-sm text-muted-foreground">
            vs {change.period}
          </span>
        </div>
      )}
    </div>
  );
};

// Composants spécialisés pour les KPIs du trading bot
export const ProfitKpiCard: React.FC<Omit<KpiCardProps, 'formatter'>> = (props) => (
  <KpiCard
    {...props}
    formatter={(value) => `$${value.toLocaleString('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`}
  />
);

export const PercentageKpiCard: React.FC<Omit<KpiCardProps, 'formatter'>> = (props) => (
  <KpiCard
    {...props}
    formatter={(value) => `${value.toFixed(2)}%`}
  />
);

export const CountKpiCard: React.FC<Omit<KpiCardProps, 'formatter'>> = (props) => (
  <KpiCard
    {...props}
    formatter={(value) => value.toLocaleString('fr-FR')}
  />
); 