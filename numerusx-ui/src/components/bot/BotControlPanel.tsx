import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Play, 
  Pause, 
  Square, 
  Settings, 
  Activity, 
  AlertTriangle, 
  Zap,
  Target,
  Shield,
  TrendingUp,
  Clock,
  DollarSign
} from 'lucide-react';
import { useBot } from '@/hooks/useBot';
import { toast } from 'sonner';

interface BotStatus {
  isActive: boolean;
  uptime: string;
  tradesExecuted: number;
  profitLoss: number;
  successRate: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  lastActivity: string;
  aiConfidence: number;
}

export const BotControlPanel: React.FC = () => {
  const { data: botStatus, startBot, stopBot, restartBot, updateConfig, isLoading } = useBot();
  const [showConfig, setShowConfig] = useState(false);
  const [riskLevel, setRiskLevel] = useState([2]); // 1-5 scale
  const [maxTradeAmount, setMaxTradeAmount] = useState([100]);
  const [autoRebalance, setAutoRebalance] = useState(true);
  const [emergencyStop, setEmergencyStop] = useState(false);

  const mockStatus: BotStatus = {
    isActive: botStatus?.isActive || false,
    uptime: botStatus?.uptime || '2h 15m',
    tradesExecuted: botStatus?.tradesExecuted || 24,
    profitLoss: botStatus?.profitLoss || 156.78,
    successRate: botStatus?.successRate || 78.5,
    riskLevel: botStatus?.riskLevel || 'MEDIUM',
    lastActivity: botStatus?.lastActivity || '2 minutes ago',
    aiConfidence: botStatus?.aiConfidence || 85,
  };

  const handleStartBot = async () => {
    try {
      await startBot();
      toast.success('Bot démarré avec succès');
    } catch (error) {
      toast.error('Erreur lors du démarrage du bot');
    }
  };

  const handleStopBot = async () => {
    try {
      await stopBot();
      toast.success('Bot arrêté');
    } catch (error) {
      toast.error('Erreur lors de l\'arrêt du bot');
    }
  };

  const handleEmergencyStop = async () => {
    try {
      await stopBot();
      setEmergencyStop(true);
      toast.error('Arrêt d\'urgence activé');
    } catch (error) {
      toast.error('Erreur lors de l\'arrêt d\'urgence');
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'text-green-600 bg-green-50';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50';
      case 'HIGH': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="space-y-6">
      {/* Status Principal */}
      <Card className="border-l-4 border-l-yellow-600">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-600" />
              Trading Bot Status
            </CardTitle>
            <Badge 
              variant={mockStatus.isActive ? "default" : "secondary"}
              className={`${mockStatus.isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'} gap-1`}
            >
              {mockStatus.isActive ? (
                <>
                  <Activity className="h-3 w-3" />
                  ACTIF
                </>
              ) : (
                <>
                  <Pause className="h-3 w-3" />
                  INACTIF
                </>
              )}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                Uptime
              </div>
              <div className="text-2xl font-bold">{mockStatus.uptime}</div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <TrendingUp className="h-4 w-4" />
                P&L Session
              </div>
              <div className={`text-2xl font-bold ${mockStatus.profitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {mockStatus.profitLoss >= 0 ? '+' : ''}${mockStatus.profitLoss.toFixed(2)}
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Target className="h-4 w-4" />
                Taux de Réussite
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-bold">{mockStatus.successRate}%</div>
                <Progress value={mockStatus.successRate} className="h-2" />
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Shield className="h-4 w-4" />
                Niveau de Risque
              </div>
              <Badge className={getRiskColor(mockStatus.riskLevel)}>
                {mockStatus.riskLevel}
              </Badge>
            </div>
          </div>

          <Separator className="my-4" />

          {/* Métriques secondaires */}
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center">
              <div className="text-lg font-semibold">{mockStatus.tradesExecuted}</div>
              <div className="text-sm text-muted-foreground">Trades Exécutés</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold">{mockStatus.aiConfidence}%</div>
              <div className="text-sm text-muted-foreground">Confiance IA</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold">{mockStatus.lastActivity}</div>
              <div className="text-sm text-muted-foreground">Dernière Activité</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contrôles Principaux */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Contrôles Bot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              {!mockStatus.isActive ? (
                <Button 
                  onClick={handleStartBot} 
                  disabled={isLoading || emergencyStop}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Démarrer Bot
                </Button>
              ) : (
                <Button 
                  onClick={handleStopBot} 
                  disabled={isLoading}
                  variant="outline"
                  className="flex-1"
                >
                  <Pause className="h-4 w-4 mr-2" />
                  Arrêter Bot
                </Button>
              )}
              
              <Button 
                onClick={() => restartBot?.()} 
                disabled={isLoading}
                variant="outline"
              >
                <Activity className="h-4 w-4 mr-2" />
                Redémarrer
              </Button>
            </div>

            <Button 
              onClick={handleEmergencyStop} 
              disabled={isLoading || !mockStatus.isActive}
              variant="destructive"
              className="w-full"
            >
              <Square className="h-4 w-4 mr-2" />
              Arrêt d'Urgence
            </Button>

            {emergencyStop && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Arrêt d'urgence activé. Redémarrage manuel requis.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configuration Rapide</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Niveau de Risque</label>
              <Slider
                value={riskLevel}
                onValueChange={setRiskLevel}
                max={5}
                min={1}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Conservateur</span>
                <span>Agressif</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Montant Max par Trade</label>
              <Slider
                value={maxTradeAmount}
                onValueChange={setMaxTradeAmount}
                max={500}
                min={10}
                step={10}
                className="w-full"
              />
              <div className="text-center text-sm">
                ${maxTradeAmount[0]}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Rééquilibrage Auto</label>
              <Switch 
                checked={autoRebalance}
                onCheckedChange={setAutoRebalance}
              />
            </div>

            <Dialog open={showConfig} onOpenChange={setShowConfig}>
              <DialogTrigger asChild>
                <Button variant="outline" className="w-full">
                  <Settings className="h-4 w-4 mr-2" />
                  Configuration Avancée
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Configuration Avancée du Bot</DialogTitle>
                </DialogHeader>
                
                <Tabs defaultValue="risk" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="risk">Risque</TabsTrigger>
                    <TabsTrigger value="strategy">Stratégie</TabsTrigger>
                    <TabsTrigger value="ai">IA</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="risk" className="space-y-4">
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium">Stop Loss (%)</label>
                        <Slider defaultValue={[5]} max={20} min={1} step={0.5} />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Take Profit (%)</label>
                        <Slider defaultValue={[10]} max={50} min={2} step={0.5} />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Max Drawdown (%)</label>
                        <Slider defaultValue={[15]} max={30} min={5} step={1} />
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="strategy" className="space-y-4">
                    <div className="text-center text-muted-foreground">
                      Configuration des stratégies de trading
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="ai" className="space-y-4">
                    <div className="text-center text-muted-foreground">
                      Paramètres de l'Agent IA
                    </div>
                  </TabsContent>
                </Tabs>
              </DialogContent>
            </Dialog>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default BotControlPanel; 
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Play, 
  Pause, 
  Square, 
  Settings, 
  Activity, 
  AlertTriangle, 
  Zap,
  Target,
  Shield,
  TrendingUp,
  Clock,
  DollarSign
} from 'lucide-react';
import { useBot } from '@/hooks/useBot';
import { toast } from 'sonner';

interface BotStatus {
  isActive: boolean;
  uptime: string;
  tradesExecuted: number;
  profitLoss: number;
  successRate: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  lastActivity: string;
  aiConfidence: number;
}

export const BotControlPanel: React.FC = () => {
  const { data: botStatus, startBot, stopBot, restartBot, updateConfig, isLoading } = useBot();
  const [showConfig, setShowConfig] = useState(false);
  const [riskLevel, setRiskLevel] = useState([2]); // 1-5 scale
  const [maxTradeAmount, setMaxTradeAmount] = useState([100]);
  const [autoRebalance, setAutoRebalance] = useState(true);
  const [emergencyStop, setEmergencyStop] = useState(false);

  const mockStatus: BotStatus = {
    isActive: botStatus?.isActive || false,
    uptime: botStatus?.uptime || '2h 15m',
    tradesExecuted: botStatus?.tradesExecuted || 24,
    profitLoss: botStatus?.profitLoss || 156.78,
    successRate: botStatus?.successRate || 78.5,
    riskLevel: botStatus?.riskLevel || 'MEDIUM',
    lastActivity: botStatus?.lastActivity || '2 minutes ago',
    aiConfidence: botStatus?.aiConfidence || 85,
  };

  const handleStartBot = async () => {
    try {
      await startBot();
      toast.success('Bot démarré avec succès');
    } catch (error) {
      toast.error('Erreur lors du démarrage du bot');
    }
  };

  const handleStopBot = async () => {
    try {
      await stopBot();
      toast.success('Bot arrêté');
    } catch (error) {
      toast.error('Erreur lors de l\'arrêt du bot');
    }
  };

  const handleEmergencyStop = async () => {
    try {
      await stopBot();
      setEmergencyStop(true);
      toast.error('Arrêt d\'urgence activé');
    } catch (error) {
      toast.error('Erreur lors de l\'arrêt d\'urgence');
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'text-green-600 bg-green-50';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50';
      case 'HIGH': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="space-y-6">
      {/* Status Principal */}
      <Card className="border-l-4 border-l-yellow-600">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-600" />
              Trading Bot Status
            </CardTitle>
            <Badge 
              variant={mockStatus.isActive ? "default" : "secondary"}
              className={`${mockStatus.isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'} gap-1`}
            >
              {mockStatus.isActive ? (
                <>
                  <Activity className="h-3 w-3" />
                  ACTIF
                </>
              ) : (
                <>
                  <Pause className="h-3 w-3" />
                  INACTIF
                </>
              )}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                Uptime
              </div>
              <div className="text-2xl font-bold">{mockStatus.uptime}</div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <TrendingUp className="h-4 w-4" />
                P&L Session
              </div>
              <div className={`text-2xl font-bold ${mockStatus.profitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {mockStatus.profitLoss >= 0 ? '+' : ''}${mockStatus.profitLoss.toFixed(2)}
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Target className="h-4 w-4" />
                Taux de Réussite
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-bold">{mockStatus.successRate}%</div>
                <Progress value={mockStatus.successRate} className="h-2" />
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Shield className="h-4 w-4" />
                Niveau de Risque
              </div>
              <Badge className={getRiskColor(mockStatus.riskLevel)}>
                {mockStatus.riskLevel}
              </Badge>
            </div>
          </div>

          <Separator className="my-4" />

          {/* Métriques secondaires */}
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center">
              <div className="text-lg font-semibold">{mockStatus.tradesExecuted}</div>
              <div className="text-sm text-muted-foreground">Trades Exécutés</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold">{mockStatus.aiConfidence}%</div>
              <div className="text-sm text-muted-foreground">Confiance IA</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold">{mockStatus.lastActivity}</div>
              <div className="text-sm text-muted-foreground">Dernière Activité</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contrôles Principaux */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Contrôles Bot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              {!mockStatus.isActive ? (
                <Button 
                  onClick={handleStartBot} 
                  disabled={isLoading || emergencyStop}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Démarrer Bot
                </Button>
              ) : (
                <Button 
                  onClick={handleStopBot} 
                  disabled={isLoading}
                  variant="outline"
                  className="flex-1"
                >
                  <Pause className="h-4 w-4 mr-2" />
                  Arrêter Bot
                </Button>
              )}
              
              <Button 
                onClick={() => restartBot?.()} 
                disabled={isLoading}
                variant="outline"
              >
                <Activity className="h-4 w-4 mr-2" />
                Redémarrer
              </Button>
            </div>

            <Button 
              onClick={handleEmergencyStop} 
              disabled={isLoading || !mockStatus.isActive}
              variant="destructive"
              className="w-full"
            >
              <Square className="h-4 w-4 mr-2" />
              Arrêt d'Urgence
            </Button>

            {emergencyStop && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Arrêt d'urgence activé. Redémarrage manuel requis.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configuration Rapide</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Niveau de Risque</label>
              <Slider
                value={riskLevel}
                onValueChange={setRiskLevel}
                max={5}
                min={1}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Conservateur</span>
                <span>Agressif</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Montant Max par Trade</label>
              <Slider
                value={maxTradeAmount}
                onValueChange={setMaxTradeAmount}
                max={500}
                min={10}
                step={10}
                className="w-full"
              />
              <div className="text-center text-sm">
                ${maxTradeAmount[0]}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Rééquilibrage Auto</label>
              <Switch 
                checked={autoRebalance}
                onCheckedChange={setAutoRebalance}
              />
            </div>

            <Dialog open={showConfig} onOpenChange={setShowConfig}>
              <DialogTrigger asChild>
                <Button variant="outline" className="w-full">
                  <Settings className="h-4 w-4 mr-2" />
                  Configuration Avancée
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Configuration Avancée du Bot</DialogTitle>
                </DialogHeader>
                
                <Tabs defaultValue="risk" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="risk">Risque</TabsTrigger>
                    <TabsTrigger value="strategy">Stratégie</TabsTrigger>
                    <TabsTrigger value="ai">IA</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="risk" className="space-y-4">
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium">Stop Loss (%)</label>
                        <Slider defaultValue={[5]} max={20} min={1} step={0.5} />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Take Profit (%)</label>
                        <Slider defaultValue={[10]} max={50} min={2} step={0.5} />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Max Drawdown (%)</label>
                        <Slider defaultValue={[15]} max={30} min={5} step={1} />
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="strategy" className="space-y-4">
                    <div className="text-center text-muted-foreground">
                      Configuration des stratégies de trading
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="ai" className="space-y-4">
                    <div className="text-center text-muted-foreground">
                      Paramètres de l'Agent IA
                    </div>
                  </TabsContent>
                </Tabs>
              </DialogContent>
            </Dialog>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default BotControlPanel; 