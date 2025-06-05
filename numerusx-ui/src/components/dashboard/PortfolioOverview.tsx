import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Chart } from '@/components/ui/chart';
import { TrendingUp, TrendingDown, DollarSign, Target, Zap, Activity } from 'lucide-react';
import { usePortfolio } from '@/hooks/usePortfolio';

interface PortfolioMetric {
  label: string;
  value: string;
  change: string;
  changeType: 'increase' | 'decrease' | 'neutral';
  icon: React.ReactNode;
  progress?: number;
}

export const PortfolioOverview: React.FC = () => {
  const { data: portfolio, isLoading } = usePortfolio();

  const metrics: PortfolioMetric[] = [
    {
      label: 'Valeur Totale',
      value: portfolio?.totalValue ? `$${portfolio.totalValue.toLocaleString()}` : '$0',
      change: portfolio?.dailyChange ? `${portfolio.dailyChange > 0 ? '+' : ''}${portfolio.dailyChange.toFixed(2)}%` : '0%',
      changeType: portfolio?.dailyChange > 0 ? 'increase' : portfolio?.dailyChange < 0 ? 'decrease' : 'neutral',
      icon: <DollarSign className="h-4 w-4" />,
    },
    {
      label: 'P&L 24h',
      value: portfolio?.pnl24h ? `${portfolio.pnl24h > 0 ? '+' : ''}$${portfolio.pnl24h.toFixed(2)}` : '$0',
      change: portfolio?.pnl24hPercent ? `${portfolio.pnl24hPercent.toFixed(2)}%` : '0%',
      changeType: portfolio?.pnl24h > 0 ? 'increase' : portfolio?.pnl24h < 0 ? 'decrease' : 'neutral',
      icon: <TrendingUp className="h-4 w-4" />,
    },
    {
      label: 'Objectif',
      value: portfolio?.targetValue ? `$${portfolio.targetValue.toLocaleString()}` : '$10,000',
      change: `${portfolio?.targetProgress || 0}% atteint`,
      changeType: 'neutral',
      icon: <Target className="h-4 w-4" />,
      progress: portfolio?.targetProgress || 0,
    },
    {
      label: 'Bot Status',
      value: portfolio?.botActive ? 'Actif' : 'Inactif',
      change: portfolio?.botActive ? `${portfolio.tradesCount || 0} trades` : 'Arrêté',
      changeType: portfolio?.botActive ? 'increase' : 'neutral',
      icon: <Zap className="h-4 w-4" />,
    },
  ];

  const chartData = portfolio?.performanceData || [
    { time: '00:00', value: 10000 },
    { time: '04:00', value: 10150 },
    { time: '08:00', value: 10300 },
    { time: '12:00', value: 10250 },
    { time: '16:00', value: 10400 },
    { time: '20:00', value: 10380 },
    { time: '24:00', value: 10420 },
  ];

  const allocationData = portfolio?.allocations || [
    { name: 'SOL', value: 45, amount: '$4,689' },
    { name: 'USDC', value: 30, amount: '$3,126' },
    { name: 'RAY', value: 15, amount: '$1,563' },
    { name: 'ORCA', value: 10, amount: '$1,042' },
  ];

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              <div className="h-4 w-4 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-6 w-32 bg-muted animate-pulse rounded mb-2" />
              <div className="h-4 w-20 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Métriques principales */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {metric.label}
              </CardTitle>
              <div className={`${
                metric.changeType === 'increase' ? 'text-green-600' : 
                metric.changeType === 'decrease' ? 'text-red-600' : 
                'text-yellow-600'
              }`}>
                {metric.icon}
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className="flex items-center space-x-2 mt-1">
                <Badge 
                  variant={
                    metric.changeType === 'increase' ? 'default' : 
                    metric.changeType === 'decrease' ? 'destructive' : 
                    'secondary'
                  }
                  className="text-xs"
                >
                  {metric.changeType === 'increase' && <TrendingUp className="h-3 w-3 mr-1" />}
                  {metric.changeType === 'decrease' && <TrendingDown className="h-3 w-3 mr-1" />}
                  {metric.changeType === 'neutral' && <Activity className="h-3 w-3 mr-1" />}
                  {metric.change}
                </Badge>
              </div>
              {metric.progress !== undefined && (
                <div className="mt-3">
                  <Progress value={metric.progress} className="h-2" />
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Graphiques et allocations */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Performance Portfolio */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-yellow-600" />
              Performance Portfolio
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="24h" className="space-y-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="24h">24h</TabsTrigger>
                <TabsTrigger value="7d">7 jours</TabsTrigger>
                <TabsTrigger value="30d">30 jours</TabsTrigger>
                <TabsTrigger value="all">Tout</TabsTrigger>
              </TabsList>
              <TabsContent value="24h" className="space-y-4">
                <Chart
                  type="line"
                  data={{
                    labels: chartData.map(d => d.time),
                    datasets: [
                      {
                        label: 'Valeur Portfolio',
                        data: chartData.map(d => d.value),
                        borderColor: 'rgb(234, 179, 8)',
                        backgroundColor: 'rgba(234, 179, 8, 0.1)',
                        tension: 0.4,
                        fill: true,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: false,
                        ticks: {
                          callback: function(value) {
                            return '$' + value.toLocaleString();
                          },
                        },
                      },
                    },
                    plugins: {
                      legend: {
                        display: false,
                      },
                      tooltip: {
                        callbacks: {
                          label: function(context) {
                            return '$' + context.parsed.y.toLocaleString();
                          },
                        },
                      },
                    },
                  }}
                  height={300}
                />
              </TabsContent>
              {/* Autres onglets avec données différentes */}
              <TabsContent value="7d">
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  Données 7 jours à venir
                </div>
              </TabsContent>
              <TabsContent value="30d">
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  Données 30 jours à venir
                </div>
              </TabsContent>
              <TabsContent value="all">
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  Données historiques complètes à venir
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Allocation des Assets */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-yellow-600" />
              Allocation Assets
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {allocationData.map((asset, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {asset.name}
                    </Badge>
                    <span className="text-sm font-medium">{asset.amount}</span>
                  </div>
                  <span className="text-sm text-muted-foreground">{asset.value}%</span>
                </div>
                <Progress value={asset.value} className="h-2" />
              </div>
            ))}
            
            {/* Action rapide */}
            <div className="pt-4 border-t">
              <button className="w-full text-sm text-yellow-600 hover:text-yellow-700 font-medium">
                Rééquilibrer le portefeuille →
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PortfolioOverview; 
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Chart } from '@/components/ui/chart';
import { TrendingUp, TrendingDown, DollarSign, Target, Zap, Activity } from 'lucide-react';
import { usePortfolio } from '@/hooks/usePortfolio';

interface PortfolioMetric {
  label: string;
  value: string;
  change: string;
  changeType: 'increase' | 'decrease' | 'neutral';
  icon: React.ReactNode;
  progress?: number;
}

export const PortfolioOverview: React.FC = () => {
  const { data: portfolio, isLoading } = usePortfolio();

  const metrics: PortfolioMetric[] = [
    {
      label: 'Valeur Totale',
      value: portfolio?.totalValue ? `$${portfolio.totalValue.toLocaleString()}` : '$0',
      change: portfolio?.dailyChange ? `${portfolio.dailyChange > 0 ? '+' : ''}${portfolio.dailyChange.toFixed(2)}%` : '0%',
      changeType: portfolio?.dailyChange > 0 ? 'increase' : portfolio?.dailyChange < 0 ? 'decrease' : 'neutral',
      icon: <DollarSign className="h-4 w-4" />,
    },
    {
      label: 'P&L 24h',
      value: portfolio?.pnl24h ? `${portfolio.pnl24h > 0 ? '+' : ''}$${portfolio.pnl24h.toFixed(2)}` : '$0',
      change: portfolio?.pnl24hPercent ? `${portfolio.pnl24hPercent.toFixed(2)}%` : '0%',
      changeType: portfolio?.pnl24h > 0 ? 'increase' : portfolio?.pnl24h < 0 ? 'decrease' : 'neutral',
      icon: <TrendingUp className="h-4 w-4" />,
    },
    {
      label: 'Objectif',
      value: portfolio?.targetValue ? `$${portfolio.targetValue.toLocaleString()}` : '$10,000',
      change: `${portfolio?.targetProgress || 0}% atteint`,
      changeType: 'neutral',
      icon: <Target className="h-4 w-4" />,
      progress: portfolio?.targetProgress || 0,
    },
    {
      label: 'Bot Status',
      value: portfolio?.botActive ? 'Actif' : 'Inactif',
      change: portfolio?.botActive ? `${portfolio.tradesCount || 0} trades` : 'Arrêté',
      changeType: portfolio?.botActive ? 'increase' : 'neutral',
      icon: <Zap className="h-4 w-4" />,
    },
  ];

  const chartData = portfolio?.performanceData || [
    { time: '00:00', value: 10000 },
    { time: '04:00', value: 10150 },
    { time: '08:00', value: 10300 },
    { time: '12:00', value: 10250 },
    { time: '16:00', value: 10400 },
    { time: '20:00', value: 10380 },
    { time: '24:00', value: 10420 },
  ];

  const allocationData = portfolio?.allocations || [
    { name: 'SOL', value: 45, amount: '$4,689' },
    { name: 'USDC', value: 30, amount: '$3,126' },
    { name: 'RAY', value: 15, amount: '$1,563' },
    { name: 'ORCA', value: 10, amount: '$1,042' },
  ];

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              <div className="h-4 w-4 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-6 w-32 bg-muted animate-pulse rounded mb-2" />
              <div className="h-4 w-20 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Métriques principales */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {metric.label}
              </CardTitle>
              <div className={`${
                metric.changeType === 'increase' ? 'text-green-600' : 
                metric.changeType === 'decrease' ? 'text-red-600' : 
                'text-yellow-600'
              }`}>
                {metric.icon}
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className="flex items-center space-x-2 mt-1">
                <Badge 
                  variant={
                    metric.changeType === 'increase' ? 'default' : 
                    metric.changeType === 'decrease' ? 'destructive' : 
                    'secondary'
                  }
                  className="text-xs"
                >
                  {metric.changeType === 'increase' && <TrendingUp className="h-3 w-3 mr-1" />}
                  {metric.changeType === 'decrease' && <TrendingDown className="h-3 w-3 mr-1" />}
                  {metric.changeType === 'neutral' && <Activity className="h-3 w-3 mr-1" />}
                  {metric.change}
                </Badge>
              </div>
              {metric.progress !== undefined && (
                <div className="mt-3">
                  <Progress value={metric.progress} className="h-2" />
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Graphiques et allocations */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Performance Portfolio */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-yellow-600" />
              Performance Portfolio
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="24h" className="space-y-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="24h">24h</TabsTrigger>
                <TabsTrigger value="7d">7 jours</TabsTrigger>
                <TabsTrigger value="30d">30 jours</TabsTrigger>
                <TabsTrigger value="all">Tout</TabsTrigger>
              </TabsList>
              <TabsContent value="24h" className="space-y-4">
                <Chart
                  type="line"
                  data={{
                    labels: chartData.map(d => d.time),
                    datasets: [
                      {
                        label: 'Valeur Portfolio',
                        data: chartData.map(d => d.value),
                        borderColor: 'rgb(234, 179, 8)',
                        backgroundColor: 'rgba(234, 179, 8, 0.1)',
                        tension: 0.4,
                        fill: true,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: false,
                        ticks: {
                          callback: function(value) {
                            return '$' + value.toLocaleString();
                          },
                        },
                      },
                    },
                    plugins: {
                      legend: {
                        display: false,
                      },
                      tooltip: {
                        callbacks: {
                          label: function(context) {
                            return '$' + context.parsed.y.toLocaleString();
                          },
                        },
                      },
                    },
                  }}
                  height={300}
                />
              </TabsContent>
              {/* Autres onglets avec données différentes */}
              <TabsContent value="7d">
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  Données 7 jours à venir
                </div>
              </TabsContent>
              <TabsContent value="30d">
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  Données 30 jours à venir
                </div>
              </TabsContent>
              <TabsContent value="all">
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  Données historiques complètes à venir
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Allocation des Assets */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-yellow-600" />
              Allocation Assets
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {allocationData.map((asset, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {asset.name}
                    </Badge>
                    <span className="text-sm font-medium">{asset.amount}</span>
                  </div>
                  <span className="text-sm text-muted-foreground">{asset.value}%</span>
                </div>
                <Progress value={asset.value} className="h-2" />
              </div>
            ))}
            
            {/* Action rapide */}
            <div className="pt-4 border-t">
              <button className="w-full text-sm text-yellow-600 hover:text-yellow-700 font-medium">
                Rééquilibrer le portefeuille →
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PortfolioOverview; 