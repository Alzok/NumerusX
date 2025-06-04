import React from 'react';
import { ProfitKpiCard, PercentageKpiCard, CountKpiCard } from '@/components/ui/kpi-card';
import { PortfolioChart } from '@/components/charts/PortfolioChart';
import { useBotStatus } from '@/hooks/useBot';
import { usePortfolioSnapshot, usePortfolioHistory } from '@/hooks/usePortfolio';
import { useTrades } from '@/hooks/useTrades';
import { TradeEntry } from '@/lib/apiClient';
import { Bot, DollarSign, TrendingUp, Activity, AlertTriangle } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const { data: botStatus, isLoading: botLoading, error: botError } = useBotStatus();
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
    <div className="container mx-auto p-4 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        
        {/* Statut du Bot */}
        <div className="flex items-center space-x-4">
          {botError && (
            <div className="flex items-center space-x-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              <span className="text-sm">Erreur connexion bot</span>
            </div>
          )}
          {botStatus && (
            <div className={`flex items-center space-x-2 px-3 py-2 rounded-full text-sm font-medium ${
              botStatus.is_running 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              <Bot className="h-4 w-4" />
              <span>{botStatus.is_running ? 'Bot Actif' : 'Bot Arrêté'}</span>
            </div>
          )}
        </div>
      </div>

      {/* Portfolio Chart */}
      <div className="grid grid-cols-1 gap-6">
        <PortfolioChart 
          data={portfolioHistory} 
          timeframe="7d"
          isLoading={historyLoading}
        />
      </div>

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
        <div className="bg-card rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Positions Actuelles</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {portfolio.positions.map((position: any, index: number) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{position.asset}</span>
                  <span className="text-sm text-muted-foreground">
                    ${position.value_usd.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="text-sm text-muted-foreground">
                  <div>Quantité: {position.amount.toLocaleString('fr-FR', { maximumFractionDigits: 6 })}</div>
                  <div>Prix moyen: ${position.avg_buy_price.toFixed(4)}</div>
                  <div>Prix actuel: ${position.current_price.toFixed(4)}</div>
                </div>
                <div className={`text-sm font-medium mt-2 ${
                  position.current_price > position.avg_buy_price ? 'text-green-600' : 'text-red-600'
                }`}>
                  {((position.current_price - position.avg_buy_price) / position.avg_buy_price * 100).toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-card rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Activité Récente</h2>
        {tradesLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <div className="h-10 w-10 bg-gray-200 rounded-full animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse" />
                  <div className="h-3 w-1/2 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        ) : recentTrades.length > 0 ? (
          <div className="space-y-3">
            {recentTrades.slice(0, 5).map((trade: any) => (
              <div key={trade.trade_id} className="flex items-center justify-between py-2 border-b last:border-b-0">
                <div className="flex items-center space-x-3">
                  <div className={`h-3 w-3 rounded-full ${
                    trade.type === 'BUY' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <div>
                    <span className="font-medium">{trade.type} {trade.pair}</span>
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
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground">Aucune activité récente</p>
        )}
      </div>
    </div>
  );
};

export default DashboardPage; 