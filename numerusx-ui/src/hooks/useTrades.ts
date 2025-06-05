import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { apiClient, TradeEntry } from '@/lib/apiClient';

export interface UseTradesOptions {
  limit?: number;
  enabled?: boolean;
}

/**
 * Hook pour récupérer l'historique des trades avec pagination
 */
export const useTrades = (options: UseTradesOptions = {}) => {
  const { limit = 50, enabled = true } = options;

  return useQuery({
    queryKey: ['trades', { limit }],
    queryFn: () => apiClient.getTradeHistory(limit, 0),
    enabled,
    staleTime: 30 * 1000, // 30 secondes
    refetchInterval: 60 * 1000, // Actualiser toutes les minutes
  });
};

/**
 * Hook pour récupérer les trades avec pagination infinie
 */
export const useInfiniteTrades = (options: { limit?: number; enabled?: boolean } = {}) => {
  const { limit = 20, enabled = true } = options;

  return useInfiniteQuery({
    queryKey: ['trades', 'infinite', { limit }],
    queryFn: ({ pageParam = 0 }) => apiClient.getTradeHistory(limit, pageParam),
    enabled,
    initialPageParam: 0,
    getNextPageParam: (lastPage: TradeEntry[], allPages: TradeEntry[][]) => {
      // Si la dernière page a moins d'éléments que la limite, on est à la fin
      if (lastPage.length < limit) return undefined;
      // Sinon, calculer l'offset suivant
      return allPages.flat().length;
    },
    staleTime: 30 * 1000, // 30 secondes
    refetchInterval: 60 * 1000, // Actualiser toutes les minutes
  });
};
