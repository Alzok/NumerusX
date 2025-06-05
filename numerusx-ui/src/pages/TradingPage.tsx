import React, { useState } from 'react';
import { TradesTable } from '@/components/ui/trades-table';
import { TradingForm } from '@/components/ui/trading-form';
import { useTrades } from '@/hooks/useTrades';
import { TrendingUp, BarChart3, AlertCircle, Target, DollarSign, Percent, Clock, Filter } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';

const TradingPage: React.FC = () => {
  const [timeFilter, setTimeFilter] = useState('24h');
  const [typeFilter, setTypeFilter] = useState('all');
  const { data: trades = [], isLoading, error, refetch } = useTrades({ limit: 50 });

  const handleTradeSuccess = (trade: any) => {
    console.log('✅ Trade executed successfully:', trade);
    refetch();
  };

  const handleTradeError = (error: any) => {
    console.error('❌ Trade execution failed:', error);
  };

  // Calculate advanced statistics
  const buyTrades = trades.filter((t: any) => t.type === 'BUY');
  const sellTrades = trades.filter((t: any) => t.type === 'SELL');
  const completedTrades = trades.filter((t: any) => t.status === 'COMPLETED');
  
  const totalVolume = trades.reduce((sum: number, trade: any) => sum + (trade.amount_usd || 0), 0);
  const avgTradeSize = trades.length > 0 ? totalVolume / trades.length : 0;
  const successRate = trades.length > 0 ? (completedTrades.length / trades.length) * 100 : 0;
  
  // P&L calculation (simplified)
  const totalPnL = trades.reduce((sum: number, trade: any) => {
    if (trade.status === 'COMPLETED' && trade.pnl) {
      return sum + trade.pnl;
    }
    return sum;
  }, 0);

  const winningTrades = trades.filter((t: any) => t.pnl && t.pnl > 0).length;
  const losingTrades = trades.filter((t: any) => t.pnl && t.pnl < 0).length;
  const winRate = (winningTrades + losingTrades) > 0 ? (winningTrades / (winningTrades + losingTrades)) * 100 : 0;

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
          <Tabs defaultValue="stats" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="stats">Statistiques</TabsTrigger>
              <TabsTrigger value="performance">Performance</TabsTrigger>
              <TabsTrigger value="filters">Filtres</TabsTrigger>
            </TabsList>
            
            <TabsContent value="stats" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Métriques de Trading
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center space-y-2">
                      <div className="flex items-center justify-center">
                        <Target className="h-4 w-4 text-muted-foreground mr-1" />
                      </div>
                      <div className="text-2xl font-bold">{trades.length}</div>
                      <Badge variant="outline" className="text-xs">Total Trades</Badge>
                    </div>
                    
                    <div className="text-center space-y-2">
                      <div className="flex items-center justify-center">
                        <DollarSign className="h-4 w-4 text-green-600 mr-1" />
                      </div>
                      <div className="text-2xl font-bold text-green-600">
                        ${totalVolume.toLocaleString()}
                      </div>
                      <Badge className="bg-green-600 hover:bg-green-700 text-xs">Volume Total</Badge>
                    </div>
                    
                    <div className="text-center space-y-2">
                      <div className="flex items-center justify-center">
                        <Percent className="h-4 w-4 text-blue-600 mr-1" />
                      </div>
                      <div className="text-2xl font-bold text-blue-600">
                        {successRate.toFixed(1)}%
                      </div>
                      <Badge variant="secondary" className="text-xs">Taux Succès</Badge>
                    </div>
                    
                    <div className="text-center space-y-2">
                      <div className="flex items-center justify-center">
                        <Clock className="h-4 w-4 text-purple-600 mr-1" />
                      </div>
                      <div className="text-2xl font-bold text-purple-600">
                        ${avgTradeSize.toFixed(0)}
                      </div>
                      <Badge variant="outline" className="text-xs">Taille Moy.</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="performance" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Performance & P&L</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center space-y-2 p-4 border rounded-lg">
                      <div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
                      </div>
                      <Badge variant={totalPnL >= 0 ? "default" : "destructive"} className="text-xs">
                        P&L Total
                      </Badge>
                    </div>
                    
                    <div className="text-center space-y-2 p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{winningTrades}</div>
                      <Badge className="bg-green-600 hover:bg-green-700 text-xs">Trades Gagnants</Badge>
                    </div>
                    
                    <div className="text-center space-y-2 p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-red-600">{losingTrades}</div>
                      <Badge variant="destructive" className="text-xs">Trades Perdants</Badge>
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Taux de Réussite</span>
                      <span className="font-medium">{winRate.toFixed(1)}%</span>
                    </div>
                    <Progress value={winRate} className="h-2" />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div className="text-center">
                      <div className="text-lg font-semibold text-green-600">{buyTrades.length}</div>
                      <div className="text-sm text-muted-foreground">Ordres d'Achat</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-red-600">{sellTrades.length}</div>
                      <div className="text-sm text-muted-foreground">Ordres de Vente</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="filters" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Filter className="h-5 w-5" />
                    Filtres & Recherche
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Période</label>
                      <Select value={timeFilter} onValueChange={setTimeFilter}>
                        <SelectTrigger>
                          <SelectValue placeholder="Sélectionner une période" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1h">Dernière heure</SelectItem>
                          <SelectItem value="24h">Dernières 24h</SelectItem>
                          <SelectItem value="7d">7 derniers jours</SelectItem>
                          <SelectItem value="30d">30 derniers jours</SelectItem>
                          <SelectItem value="all">Tous les trades</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Type de Trade</label>
                      <Select value={typeFilter} onValueChange={setTypeFilter}>
                        <SelectTrigger>
                          <SelectValue placeholder="Sélectionner un type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Tous les types</SelectItem>
                          <SelectItem value="BUY">Achats uniquement</SelectItem>
                          <SelectItem value="SELL">Ventes uniquement</SelectItem>
                          <SelectItem value="COMPLETED">Trades complétés</SelectItem>
                          <SelectItem value="PENDING">Trades en cours</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 pt-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        setTimeFilter('24h');
                        setTypeFilter('all');
                      }}
                    >
                      Réinitialiser
                    </Button>
                    <Button variant="outline" size="sm">
                      Exporter CSV
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
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
