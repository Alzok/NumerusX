import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/apiClient';

export interface UsePortfolioOptions {
  enabled?: boolean;
  refetchInterval?: number;
}

/**
 * Hook pour récupérer le snapshot du portfolio
 */
export const usePortfolioSnapshot = () => {
  return useQuery({
    queryKey: ['portfolio', 'snapshot'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/portfolio/snapshot');
      return response.data;
    },
    staleTime: 30 * 1000, // 30 secondes
    refetchInterval: 60 * 1000, // Actualiser toutes les 60 secondes
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