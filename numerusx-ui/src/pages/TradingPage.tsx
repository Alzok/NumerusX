import React from 'react';
import { TradesTable } from '@/components/ui/trades-table';
import { TradingForm } from '@/components/ui/trading-form';
import { useTrades } from '@/hooks/useTrades';
import { Zap, TrendingUp } from 'lucide-react';

const TradingPage: React.FC = () => {
  const { data: trades = [], isLoading, error, refetch } = useTrades({ limit: 50 });

  const handleTradeSuccess = (trade: any) => {
    console.log('✅ Trade executed successfully:', trade);
    refetch();
  };

  const handleTradeError = (error: any) => {
    console.error('❌ Trade execution failed:', error);
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <TrendingUp className="h-8 w-8" />
            Trading Center
          </h1>
          <p className="text-muted-foreground">
            {trades.length} trades historiques
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">
            Erreur lors du chargement des trades : {error.message}
          </p>
          <button 
            onClick={() => refetch()}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Réessayer
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <TradingForm
            onSuccess={handleTradeSuccess}
            onError={handleTradeError}
          />
        </div>

        <div className="lg:col-span-2">
          <div className="bg-card rounded-lg border p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5 text-blue-600" />
              Statistiques Rapides
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg border">
                <div className="text-2xl font-bold text-blue-600">
                  {trades.length}
                </div>
                <div className="text-sm text-gray-600">Total Trades</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg border">
                <div className="text-2xl font-bold text-green-600">
                  {trades.filter((t: any) => t.type === 'BUY').length}
                </div>
                <div className="text-sm text-gray-600">Achats</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg border">
                <div className="text-2xl font-bold text-red-600">
                  {trades.filter((t: any) => t.type === 'SELL').length}
                </div>
                <div className="text-sm text-gray-600">Ventes</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-card rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Historique des Trades</h2>
        <TradesTable 
          data={trades} 
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};

export default TradingPage; 