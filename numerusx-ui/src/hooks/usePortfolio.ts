import { useQuery } from '@tanstack/react-query';
import { apiClient, PortfolioSnapshot } from '@/lib/apiClient';

export interface UsePortfolioOptions {
  enabled?: boolean;
  refetchInterval?: number;
}

/**
 * Hook pour récupérer le snapshot du portfolio
 */
export const usePortfolioSnapshot = (options: UsePortfolioOptions = {}) => {
  const { enabled = true, refetchInterval = 30 * 1000 } = options; // 30 secondes par défaut

  return useQuery({
    queryKey: ['portfolio', 'snapshot'],
    queryFn: () => apiClient.getPortfolioSnapshot(),
    enabled,
    staleTime: 15 * 1000, // 15 secondes
    refetchInterval,
  });
};

/**
 * Hook pour récupérer l'historique du portfolio
 */
export const usePortfolioHistory = (days = 7, options: UsePortfolioOptions = {}) => {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['portfolio', 'history', { days }],
    queryFn: () => apiClient.getPortfolioHistory(days),
    enabled,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 60 * 1000, // Actualiser chaque minute
  });
}; 