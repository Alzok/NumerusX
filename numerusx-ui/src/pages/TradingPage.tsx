import React from 'react';
import { TradesTable } from '@/components/ui/trades-table';
import { TradingForm } from '@/components/ui/trading-form';
import { useTrades } from '@/hooks/useTrades';
import { TrendingUp, BarChart3, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const TradingPage: React.FC = () => {
  const { data: trades = [], isLoading, error, refetch } = useTrades({ limit: 50 });

  const handleTradeSuccess = (trade: any) => {
    console.log('✅ Trade executed successfully:', trade);
    refetch();
  };

  const handleTradeError = (error: any) => {
    console.error('❌ Trade execution failed:', error);
  };

  const buyTrades = trades.filter((t: any) => t.type === 'BUY').length;
  const sellTrades = trades.filter((t: any) => t.type === 'SELL').length;

  return (
    <div className="space-y-6">
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
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Erreur lors du chargement des trades : {error.message}
            <Button 
              variant="link" 
              className="ml-2 h-auto p-0 text-destructive underline"
              onClick={() => refetch()}
            >
              Réessayer
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <TradingForm
            onSuccess={handleTradeSuccess}
            onError={handleTradeError}
          />
        </div>

        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Statistiques Rapides
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="text-center p-4">
                    <div className="text-2xl font-bold mb-1">
                      {trades.length}
                    </div>
                    <Badge variant="outline" className="text-xs">
                      Total Trades
                    </Badge>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="text-center p-4">
                    <div className="text-2xl font-bold text-green-600 mb-1">
                      {buyTrades}
                    </div>
                    <Badge className="bg-green-600 hover:bg-green-700 text-xs">
                      Achats
                    </Badge>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="text-center p-4">
                    <div className="text-2xl font-bold text-red-600 mb-1">
                      {sellTrades}
                    </div>
                    <Badge variant="destructive" className="text-xs">
                      Ventes
                    </Badge>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Historique des Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <TradesTable 
            data={trades} 
            isLoading={isLoading}
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default TradingPage; 