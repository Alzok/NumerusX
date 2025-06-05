import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/apiClient';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, DollarSign, AlertTriangle } from 'lucide-react';

interface TradingFormProps {
  onSuccess?: (trade: any) => void;
  onError?: (error: any) => void;
  disabled?: boolean;
}

interface TradingFormData {
  pair: string;
  type: 'BUY' | 'SELL';
  amount_usd: number;
}

export const TradingForm: React.FC<TradingFormProps> = ({
  onSuccess,
  onError,
  disabled = false,
}) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<TradingFormData>({
    pair: 'SOL/USDC',
    type: 'BUY',
    amount_usd: 100,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [lastTrade, setLastTrade] = useState<any>(null);

  // Validation simple
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.pair || !formData.pair.includes('/')) {
      newErrors.pair = 'Format requis: TOKEN/USDC';
    }

    if (formData.amount_usd < 10) {
      newErrors.amount_usd = 'Montant minimum: $10';
    }

    if (formData.amount_usd > 100000) {
      newErrors.amount_usd = 'Montant maximum: $100,000';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Mutation pour exécuter le trade
  const executeTradeMutation = useMutation({
    mutationFn: (data: TradingFormData) => apiClient.executeManualTrade(data),
    onSuccess: (result) => {
      setLastTrade(result);
      // Invalider les caches
      queryClient.invalidateQueries({ queryKey: ['trades'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      
      onSuccess?.(result);
      // Reset form
      setFormData({
        pair: 'SOL/USDC',
        type: 'BUY',
        amount_usd: 100,
      });
    },
    onError: (error) => {
      console.error('Trade execution failed:', error);
      onError?.(error);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      executeTradeMutation.mutate(formData);
    }
  };

  const updateFormData = (field: keyof TradingFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user types
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="bg-card rounded-lg border p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Trading Manuel</h3>
        <Badge className={formData.type === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
          {formData.type === 'BUY' ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
          {formData.type}
        </Badge>
      </div>

      {/* Succès */}
      {lastTrade && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <p className="text-sm text-green-800">
            ✅ Trade exécuté: {lastTrade.type} {lastTrade.pair} pour ${lastTrade.amount_usd}
          </p>
        </div>
      )}

      {/* Erreur */}
      {executeTradeMutation.error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <p className="text-sm text-red-800">
              Erreur: {(executeTradeMutation.error as Error).message}
            </p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Paire */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Paire de Trading</label>
          <Input
            value={formData.pair}
            onChange={(e) => updateFormData('pair', e.target.value)}
            placeholder="SOL/USDC"
            disabled={disabled || executeTradeMutation.isPending}
            className={errors.pair ? 'border-red-500' : ''}
          />
          {errors.pair && <p className="text-sm text-red-600">{errors.pair}</p>}
        </div>

        {/* Type */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Type de Trade</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => updateFormData('type', 'BUY')}
              disabled={disabled || executeTradeMutation.isPending}
              className={`p-3 border rounded-md text-center transition-colors ${
                formData.type === 'BUY' 
                  ? 'border-green-500 bg-green-50 text-green-700' 
                  : 'border-gray-300 hover:border-green-300'
              }`}
            >
              <TrendingUp className="h-4 w-4 mx-auto mb-1" />
              <span className="text-sm font-medium">ACHETER</span>
            </button>
            <button
              type="button"
              onClick={() => updateFormData('type', 'SELL')}
              disabled={disabled || executeTradeMutation.isPending}
              className={`p-3 border rounded-md text-center transition-colors ${
                formData.type === 'SELL' 
                  ? 'border-red-500 bg-red-50 text-red-700' 
                  : 'border-gray-300 hover:border-red-300'
              }`}
            >
              <TrendingDown className="h-4 w-4 mx-auto mb-1" />
              <span className="text-sm font-medium">VENDRE</span>
            </button>
          </div>
        </div>

        {/* Montant */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Montant (USD)</label>
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="number"
              value={formData.amount_usd}
              onChange={(e) => updateFormData('amount_usd', parseFloat(e.target.value) || 0)}
              step="0.01"
              min="10"
              max="100000"
              placeholder="100.00"
              disabled={disabled || executeTradeMutation.isPending}
              className={`pl-10 ${errors.amount_usd ? 'border-red-500' : ''}`}
            />
          </div>
          {errors.amount_usd && <p className="text-sm text-red-600">{errors.amount_usd}</p>}
          <p className="text-xs text-gray-500">
            Montant: ${formData.amount_usd.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}
          </p>
        </div>

        {/* Bouton */}
        <Button
          type="submit"
          disabled={disabled || executeTradeMutation.isPending}
          className={`w-full ${
            formData.type === 'BUY' 
              ? 'bg-green-600 hover:bg-green-700' 
              : 'bg-red-600 hover:bg-red-700'
          }`}
        >
          {executeTradeMutation.isPending ? (
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Exécution...</span>
            </div>
          ) : (
            `${formData.type === 'BUY' ? 'ACHETER' : 'VENDRE'} $${formData.amount_usd}`
          )}
        </Button>
      </form>

      {/* Avertissement */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
        <p className="text-xs text-yellow-800">
          ⚠️ Les trades manuels peuvent affecter la stratégie du bot.
        </p>
      </div>
    </div>

  );
};

export default TradingForm;
