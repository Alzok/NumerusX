import React from 'react';
import { ProfitKpiCard, CountKpiCard } from '@/components/ui/kpi-card';
import { PortfolioChart } from '@/components/charts/PortfolioChart';
import { useBotStatus } from '@/hooks/useBot';
import { usePortfolioSnapshot, usePortfolioHistory } from '@/hooks/usePortfolio';
import { useTrades } from '@/hooks/useTrades';
import { TradeEntry } from '@/lib/apiClient';
import { Bot, DollarSign, TrendingUp, Activity, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';

const DashboardPage: React.FC = () => {
  const { data: botStatus, error: botError } = useBotStatus();
  const { data: portfolio, isLoading: portfolioLoading } = usePortfolioSnapshot();
  const { data: portfolioHistory = [], isLoading: historyLoading } = usePortfolioHistory(7);
  const { data: recentTrades = [], isLoading: tradesLoading } = useTrades({ limit: 10 });

  // Calculer les métriques
  const activeTrades = recentTrades.filter((trade: TradeEntry) => trade.status === 'PENDING').length;
  const completedTrades24h = recentTrades.filter((trade: TradeEntry) => {
    const tradeDate = new Date(trade.timestamp_utc);
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
    return tradeDate > yesterday && trade.status === 'COMPLETED';
  }).length;

  const pnl24h = portfolio?.pnl_24h_usd || 0;
  const totalValue = portfolio?.total_value_usd || 0;
  const pnlPercentage = totalValue > 0 ? (pnl24h / totalValue) * 100 : 0;

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        
        {/* Statut du Bot */}
        <div className="flex items-center space-x-4">
          {botError && (
            <Alert variant="destructive" className="w-auto">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Erreur connexion bot
              </AlertDescription>
            </Alert>
          )}
          {botStatus && (
            <Badge 
              variant={botStatus.is_running ? "default" : "secondary"}
              className={`px-3 py-2 ${
                botStatus.is_running 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-slate-600 hover:bg-slate-700'
              }`}
            >
              <Bot className="h-4 w-4 mr-2" />
              {botStatus.is_running ? 'Bot Actif' : 'Bot Arrêté'}
            </Badge>
          )}
        </div>
      </div>

      {/* Portfolio Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Évolution du Portfolio</CardTitle>
        </CardHeader>
        <CardContent>
          <PortfolioChart 
            data={portfolioHistory} 
            timeframe="7d"
            isLoading={historyLoading}
          />
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <ProfitKpiCard
          title="Valeur Portfolio"
          value={totalValue}
          icon={<DollarSign className="h-6 w-6" />}
          isLoading={portfolioLoading}
        />
        
        <ProfitKpiCard
          title="P&L 24h"
          value={pnl24h}
          change={{
            value: pnl24h,
            percentage: pnlPercentage,
            period: '24h'
          }}
          icon={<TrendingUp className="h-6 w-6" />}
          isLoading={portfolioLoading}
        />
        
        <CountKpiCard
          title="Trades Actifs"
          value={activeTrades}
          icon={<Activity className="h-6 w-6" />}
          isLoading={tradesLoading}
        />
        
        <CountKpiCard
          title="Trades 24h"
          value={completedTrades24h}
          icon={<Activity className="h-6 w-6" />}
          isLoading={tradesLoading}
        />
      </div>

      {/* Portfolio Positions */}
      {portfolio && portfolio.positions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Positions Actuelles</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {portfolio.positions.map((position: any, index: number) => (
                <Card key={index} className="border-muted">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{position.asset}</span>
                      <Badge variant="outline">
                        ${position.value_usd.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
                      </Badge>
                    </div>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <div>Quantité: {position.amount.toLocaleString('fr-FR', { maximumFractionDigits: 6 })}</div>
                      <div>Prix moyen: ${position.avg_buy_price.toFixed(4)}</div>
                      <div>Prix actuel: ${position.current_price.toFixed(4)}</div>
                    </div>
                    <Separator className="my-2" />
                    <Badge 
                      variant={position.current_price > position.avg_buy_price ? "default" : "destructive"}
                      className={position.current_price > position.avg_buy_price ? 'bg-green-600' : ''}
                    >
                      {((position.current_price - position.avg_buy_price) / position.avg_buy_price * 100).toFixed(2)}%
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Activité Récente</CardTitle>
        </CardHeader>
        <CardContent>
          {tradesLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : recentTrades.length > 0 ? (
            <div className="space-y-3">
              {recentTrades.slice(0, 5).map((trade: any, index: number) => (
                <div key={trade.trade_id}>
                  <div className="flex items-center justify-between py-3">
                    <div className="flex items-center space-x-3">
                      <Badge 
                        variant={trade.type === 'BUY' ? "default" : "destructive"}
                        className={`w-16 justify-center ${
                          trade.type === 'BUY' ? 'bg-green-600' : 'bg-red-600'
                        }`}
                      >
                        {trade.type}
                      </Badge>
                      <div>
                        <span className="font-medium">{trade.pair}</span>
                        <div className="text-sm text-muted-foreground">
                          {trade.amount_tokens.toLocaleString('fr-FR', { maximumFractionDigits: 6 })} tokens
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">
                        ${trade.price_usd.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(trade.timestamp_utc).toLocaleTimeString('fr-FR')}
                      </div>
                    </div>
                  </div>
                  {index < recentTrades.slice(0, 5).length - 1 && <Separator />}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">Aucune activité récente</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardPage; 
  // Calculer les métriques
  const activeTrades = recentTrades.filter((trade: TradeEntry) => trade.status === 'PENDING').length;
  const completedTrades24h = recentTrades.filter((trade: TradeEntry) => {
    const tradeDate = new Date(trade.timestamp_utc);
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
    return tradeDate > yesterday && trade.status === 'COMPLETED';
  }).length;

  const pnl24h = portfolio?.pnl_24h_usd || 0;
  const totalValue = portfolio?.total_value_usd || 0;
  const pnlPercentage = totalValue > 0 ? (pnl24h / totalValue) * 100 : 0;

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        
        {/* Statut du Bot */}
        <div className="flex items-center space-x-4">
          {botError && (
            <Alert variant="destructive" className="w-auto">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Erreur connexion bot
              </AlertDescription>
            </Alert>
          )}
          {botStatus && (
            <Badge 
              variant={botStatus.is_running ? "default" : "secondary"}
              className={`px-3 py-2 ${
                botStatus.is_running 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-slate-600 hover:bg-slate-700'
              }`}
            >
              <Bot className="h-4 w-4 mr-2" />
              {botStatus.is_running ? 'Bot Actif' : 'Bot Arrêté'}
            </Badge>
          )}
        </div>
      </div>

      {/* Portfolio Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Évolution du Portfolio</CardTitle>
        </CardHeader>
        <CardContent>
          <PortfolioChart 
            data={portfolioHistory} 
            timeframe="7d"
            isLoading={historyLoading}
          />
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <ProfitKpiCard
          title="Valeur Portfolio"
          value={totalValue}
          icon={<DollarSign className="h-6 w-6" />}
          isLoading={portfolioLoading}
        />
        
        <ProfitKpiCard
          title="P&L 24h"
          value={pnl24h}
          change={{
            value: pnl24h,
            percentage: pnlPercentage,
            period: '24h'
          }}
          icon={<TrendingUp className="h-6 w-6" />}
          isLoading={portfolioLoading}
        />
        
        <CountKpiCard
          title="Trades Actifs"
          value={activeTrades}
          icon={<Activity className="h-6 w-6" />}
          isLoading={tradesLoading}
        />
        
        <CountKpiCard
          title="Trades 24h"
          value={completedTrades24h}
          icon={<Activity className="h-6 w-6" />}
          isLoading={tradesLoading}
        />
      </div>

      {/* Portfolio Positions */}
      {portfolio && portfolio.positions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Positions Actuelles</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {portfolio.positions.map((position: any, index: number) => (
                <Card key={index} className="border-muted">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{position.asset}</span>
                      <Badge variant="outline">
                        ${position.value_usd.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
                      </Badge>
                    </div>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <div>Quantité: {position.amount.toLocaleString('fr-FR', { maximumFractionDigits: 6 })}</div>
                      <div>Prix moyen: ${position.avg_buy_price.toFixed(4)}</div>
                      <div>Prix actuel: ${position.current_price.toFixed(4)}</div>
                    </div>
                    <Separator className="my-2" />
                    <Badge 
                      variant={position.current_price > position.avg_buy_price ? "default" : "destructive"}
                      className={position.current_price > position.avg_buy_price ? 'bg-green-600' : ''}
                    >
                      {((position.current_price - position.avg_buy_price) / position.avg_buy_price * 100).toFixed(2)}%
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Activité Récente</CardTitle>
        </CardHeader>
        <CardContent>
          {tradesLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : recentTrades.length > 0 ? (
            <div className="space-y-3">
              {recentTrades.slice(0, 5).map((trade: any, index: number) => (
                <div key={trade.trade_id}>
                  <div className="flex items-center justify-between py-3">
                    <div className="flex items-center space-x-3">
                      <Badge 
                        variant={trade.type === 'BUY' ? "default" : "destructive"}
                        className={`w-16 justify-center ${
                          trade.type === 'BUY' ? 'bg-green-600' : 'bg-red-600'
                        }`}
                      >
                        {trade.type}
                      </Badge>
                      <div>
                        <span className="font-medium">{trade.pair}</span>
                        <div className="text-sm text-muted-foreground">
                          {trade.amount_tokens.toLocaleString('fr-FR', { maximumFractionDigits: 6 })} tokens
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">
                        ${trade.price_usd.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(trade.timestamp_utc).toLocaleTimeString('fr-FR')}
                      </div>
                    </div>
                  </div>
                  {index < recentTrades.slice(0, 5).length - 1 && <Separator />}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">Aucune activité récente</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardPage; 