import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/apiClient';

/**
 * Hook pour récupérer le statut du bot
 */
export const useBotStatus = () => {
  return useQuery({
    queryKey: ['botStatus'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/bot/status');
      return response.data;
    },
    refetchInterval: 5000,
  });
};

/**
 * Hook pour démarrer le bot
 */
export const useStartBot = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.startBot(),
    onSuccess: () => {
      // Invalider le cache du statut pour récupérer les nouvelles données
      queryClient.invalidateQueries({ queryKey: ['bot', 'status'] });
    },
    onError: (error) => {
      console.error('Failed to start bot:', error);
    },
  });
};

/**
 * Hook pour arrêter le bot
 */
export const useStopBot = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.stopBot(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bot', 'status'] });
    },
    onError: (error) => {
      console.error('Failed to stop bot:', error);
    },
  });
};

/**
 * Hook pour l'arrêt d'urgence
 */
export const useEmergencyStop = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.emergencyStop(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bot', 'status'] });
      // Également invalider portfolio et trades
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['trades'] });
    },
    onError: (error) => {
      console.error('Failed to emergency stop:', error);
    },
  });
}; 