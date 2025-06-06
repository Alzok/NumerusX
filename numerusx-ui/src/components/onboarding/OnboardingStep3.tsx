import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Shield, TestTube, Zap, DollarSign, TrendingUp, AlertTriangle, 
  Info, Settings, Target, Gauge 
} from "lucide-react";

interface OnboardingStep3Props {
  data: any;
  onChange: (data: any) => void;
}

const OnboardingStep3: React.FC<OnboardingStep3Props> = ({ data, onChange }) => {
  const [operatingMode, setOperatingMode] = useState(data.operating_mode || 'test');
  const [initialBalance, setInitialBalance] = useState(data.initial_balance_usd || 1000);
  const [maxTradeSize, setMaxTradeSize] = useState(data.max_trade_size_usd || 100);
  const [riskLevel, setRiskLevel] = useState(data.risk_level || 'moderate');

  useEffect(() => {
    const newData = {
      ...data,
      operating_mode: operatingMode,
      initial_balance_usd: initialBalance,
      max_trade_size_usd: maxTradeSize,
      risk_level: riskLevel
    };
    onChange(newData);
  }, [operatingMode, initialBalance, maxTradeSize, riskLevel]);

  const operatingModes = [
    {
      id: 'test',
      name: 'Mode Test',
      icon: TestTube,
      description: 'Simulation complète sans vraies transactions',
      benefits: [
        'Aucun risque financier',
        'Apprentissage et optimisation',
        'Données de marché réelles',
        'Interface complète'
      ],
      limitations: [
        'Pas de profits réels',
        'Simulation des frais uniquement'
      ],
      recommended: true,
      color: 'bg-blue-500'
    },
    {
      id: 'production',
      name: 'Mode Production',
      icon: Zap,
      description: 'Trading réel avec de vrais fonds',
      benefits: [
        'Profits et pertes réels',
        'Transactions sur le réseau',
        'Frais de transaction réels',
        'Performance maximale'
      ],
      limitations: [
        'Risque de perte réelle',
        'Frais de transaction',
        'Responsabilité utilisateur'
      ],
      recommended: false,
      color: 'bg-red-500'
    }
  ];

  const riskLevels = [
    {
      id: 'conservative',
      name: 'Conservateur',
      description: 'Trading prudent avec des risques minimaux',
      maxTradePercent: 2,
      stopLossPercent: 5,
      takeProfitPercent: 10,
      color: 'bg-green-500',
      icon: Shield
    },
    {
      id: 'moderate',
      name: 'Modéré',
      description: 'Équilibre entre sécurité et rendement',
      maxTradePercent: 5,
      stopLossPercent: 8,
      takeProfitPercent: 15,
      color: 'bg-yellow-500',
      icon: Target
    },
    {
      id: 'aggressive',
      name: 'Agressif',
      description: 'Trading actif avec potentiel de gains élevés',
      maxTradePercent: 10,
      stopLossPercent: 12,
      takeProfitPercent: 25,
      color: 'bg-red-500',
      icon: TrendingUp
    }
  ];

  const getCurrentRiskLevel = () => {
    return riskLevels.find(level => level.id === riskLevel) || riskLevels[1];
  };

  const handleMaxTradeSizeChange = (value: number[]) => {
    setMaxTradeSize(value[0]);
  };

  return (
    <div className="space-y-6">
      <Alert>
        <Settings className="h-4 w-4" />
        <AlertDescription>
          <strong>Configuration finale:</strong> Choisissez votre mode d'utilisation et vos paramètres de trading. 
          Ces réglages déterminent comment votre bot fonctionnera.
        </AlertDescription>
      </Alert>

      {/* Operating Mode Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Gauge className="h-5 w-5" />
            <span>Mode d'Opération</span>
          </CardTitle>
          <CardDescription>
            Sélectionnez comment vous souhaitez utiliser NumerusX
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup value={operatingMode} onValueChange={setOperatingMode}>
            <div className="grid gap-4">
              {operatingModes.map((mode) => {
                const IconComponent = mode.icon;
                return (
                  <div key={mode.id} className="flex items-start space-x-3">
                    <RadioGroupItem 
                      value={mode.id} 
                      id={mode.id}
                      className="mt-6"
                    />
                    <Label htmlFor={mode.id} className="flex-1 cursor-pointer">
                      <Card className={`transition-all duration-200 ${
                        operatingMode === mode.id 
                          ? 'ring-2 ring-primary shadow-md' 
                          : 'hover:shadow-sm'
                      }`}>
                        <CardContent className="p-6">
                          <div className="space-y-4">
                            {/* Header */}
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <div className={`p-2 rounded-lg ${mode.color} bg-opacity-10`}>
                                  <IconComponent className={`h-5 w-5 text-white`} style={{color: mode.color.replace('bg-', '').replace('-500', '')}} />
                                </div>
                                <div>
                                  <div className="font-semibold text-lg">{mode.name}</div>
                                  <div className="text-sm text-muted-foreground">{mode.description}</div>
                                </div>
                              </div>
                              {mode.recommended && (
                                <Badge className="bg-green-100 text-green-800">Recommandé</Badge>
                              )}
                            </div>

                            {/* Benefits and Limitations */}
                            <div className="grid md:grid-cols-2 gap-4">
                              <div>
                                <div className="font-medium text-sm text-green-600 mb-2">Avantages:</div>
                                <ul className="space-y-1">
                                  {mode.benefits.map((benefit, index) => (
                                    <li key={index} className="text-sm text-muted-foreground flex items-center">
                                      <div className="w-1 h-1 bg-green-500 rounded-full mr-2"></div>
                                      {benefit}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                              <div>
                                <div className="font-medium text-sm text-orange-600 mb-2">Limitations:</div>
                                <ul className="space-y-1">
                                  {mode.limitations.map((limitation, index) => (
                                    <li key={index} className="text-sm text-muted-foreground flex items-center">
                                      <div className="w-1 h-1 bg-orange-500 rounded-full mr-2"></div>
                                      {limitation}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </Label>
                  </div>
                );
              })}
            </div>
          </RadioGroup>

          {operatingMode === 'production' && (
            <Alert className="mt-4" variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>Attention:</strong> En mode production, vous utilisez de vrais fonds. 
                Assurez-vous de bien comprendre les risques avant de continuer.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Portfolio Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <DollarSign className="h-5 w-5" />
            <span>Configuration du Portefeuille</span>
          </CardTitle>
          <CardDescription>
            Définissez vos paramètres financiers de base
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Initial Balance */}
          <div className="space-y-2">
            <Label htmlFor="initial-balance">
              Solde Initial {operatingMode === 'test' ? '(Simulation)' : '(USD)'}
            </Label>
            <Input
              id="initial-balance"
              type="number"
              value={initialBalance}
              onChange={(e) => setInitialBalance(Number(e.target.value))}
              min="100"
              max="100000"
              step="100"
            />
            <p className="text-sm text-muted-foreground">
              {operatingMode === 'test' 
                ? 'Montant virtuel pour la simulation' 
                : 'Montant réel que vous prévoyez d\'investir'
              }
            </p>
          </div>

          {/* Max Trade Size */}
          <div className="space-y-3">
            <Label htmlFor="max-trade-size">
              Taille Maximale par Trade: ${maxTradeSize}
            </Label>
            <Slider
              id="max-trade-size"
              min={10}
              max={Math.min(1000, initialBalance * 0.2)}
              step={10}
              value={[maxTradeSize]}
              onValueChange={handleMaxTradeSizeChange}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>$10</span>
              <span>{((maxTradeSize / initialBalance) * 100).toFixed(1)}% du portefeuille</span>
              <span>${Math.min(1000, initialBalance * 0.2)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Level Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Target className="h-5 w-5" />
            <span>Niveau de Risque</span>
          </CardTitle>
          <CardDescription>
            Choisissez votre tolérance au risque pour automatiser les paramètres de trading
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup value={riskLevel} onValueChange={setRiskLevel}>
            <div className="grid gap-3">
              {riskLevels.map((level) => {
                const IconComponent = level.icon;
                return (
                  <div key={level.id} className="flex items-center space-x-3">
                    <RadioGroupItem value={level.id} id={level.id} />
                    <Label htmlFor={level.id} className="flex-1 cursor-pointer">
                      <Card className={`transition-all duration-200 ${
                        riskLevel === level.id 
                          ? 'ring-2 ring-primary shadow-sm' 
                          : 'hover:shadow-sm'
                      }`}>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <div className={`p-2 rounded ${level.color} bg-opacity-20`}>
                                <IconComponent className="h-4 w-4" />
                              </div>
                              <div>
                                <div className="font-medium">{level.name}</div>
                                <div className="text-sm text-muted-foreground">{level.description}</div>
                              </div>
                            </div>
                            <div className="text-right text-sm">
                              <div>Max: {level.maxTradePercent}%</div>
                              <div className="text-muted-foreground">SL: {level.stopLossPercent}%</div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </Label>
                  </div>
                );
              })}
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      {/* Configuration Summary */}
      <Card className="bg-muted/50">
        <CardHeader>
          <CardTitle className="text-base">Résumé de Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="font-medium">Mode:</span>
                <Badge variant={operatingMode === 'test' ? 'secondary' : 'destructive'}>
                  {operatingModes.find(m => m.id === operatingMode)?.name}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Solde initial:</span>
                <span>${initialBalance.toLocaleString()}</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="font-medium">Max par trade:</span>
                <span>${maxTradeSize}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Profil de risque:</span>
                <Badge variant="outline">{getCurrentRiskLevel().name}</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Final Warning for Production Mode */}
      {operatingMode === 'production' && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>Mode Production Activé:</strong> Vous êtes sur le point de configurer le trading en mode réel. 
            Assurez-vous d'avoir suffisamment testé en mode simulation et de comprendre tous les risques.
          </AlertDescription>
        </Alert>
      )}

      {/* Help Text */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <strong>Recommandation:</strong> Commencez toujours par le mode test pour vous familiariser 
          avec le système avant de passer en mode production.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default OnboardingStep3; 