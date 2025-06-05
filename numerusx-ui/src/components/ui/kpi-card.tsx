import React from 'react';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

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
        return <TrendingUp className="h-4 w-4" />;
      case 'down':
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <Minus className="h-4 w-4" />;
    }
  };

  const getTrendVariant = () => {
    switch (currentTrend) {
      case 'up':
        return 'default';
      case 'down':
        return 'destructive';
      default:
        return 'secondary';
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
      <Card className={className}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <Skeleton className="h-4 w-24" />
          {icon && <Skeleton className="h-8 w-8" />}
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-32 mb-2" />
          {change && (
            <div className="flex items-center space-x-2">
              <Skeleton className="h-4 w-4" />
              <Skeleton className="h-4 w-20" />
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <p className="text-sm font-medium text-muted-foreground">
          {title}
        </p>
        {icon && (
          <div className="h-8 w-8 text-muted-foreground">
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold tracking-tight mb-2">
          {formatValue(value)}
        </div>
        
        {change && (
          <div className="flex items-center space-x-2">
            <Badge 
              variant={getTrendVariant()}
              className={cn(
                "text-xs px-2 py-1",
                currentTrend === 'up' && "bg-green-600 hover:bg-green-700",
                currentTrend === 'down' && "bg-red-600 hover:bg-red-700"
              )}
            >
              {getTrendIcon()}
              <span className="ml-1">
                {change.value > 0 ? '+' : ''}
                {formatter ? formatter(change.value) : change.value}
              </span>
            </Badge>
            <span className="text-xs text-muted-foreground">
              ({change.percentage > 0 ? '+' : ''}{change.percentage.toFixed(1)}%) vs {change.period}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
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
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

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
        return <TrendingUp className="h-4 w-4" />;
      case 'down':
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <Minus className="h-4 w-4" />;
    }
  };

  const getTrendVariant = () => {
    switch (currentTrend) {
      case 'up':
        return 'default';
      case 'down':
        return 'destructive';
      default:
        return 'secondary';
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
      <Card className={className}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <Skeleton className="h-4 w-24" />
          {icon && <Skeleton className="h-8 w-8" />}
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-32 mb-2" />
          {change && (
            <div className="flex items-center space-x-2">
              <Skeleton className="h-4 w-4" />
              <Skeleton className="h-4 w-20" />
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <p className="text-sm font-medium text-muted-foreground">
          {title}
        </p>
        {icon && (
          <div className="h-8 w-8 text-muted-foreground">
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold tracking-tight mb-2">
          {formatValue(value)}
        </div>
        
        {change && (
          <div className="flex items-center space-x-2">
            <Badge 
              variant={getTrendVariant()}
              className={cn(
                "text-xs px-2 py-1",
                currentTrend === 'up' && "bg-green-600 hover:bg-green-700",
                currentTrend === 'down' && "bg-red-600 hover:bg-red-700"
              )}
            >
              {getTrendIcon()}
              <span className="ml-1">
                {change.value > 0 ? '+' : ''}
                {formatter ? formatter(change.value) : change.value}
              </span>
            </Badge>
            <span className="text-xs text-muted-foreground">
              ({change.percentage > 0 ? '+' : ''}{change.percentage.toFixed(1)}%) vs {change.period}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
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