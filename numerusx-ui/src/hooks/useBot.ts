import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, BotStatus } from '@/lib/apiClient';

/**
 * Hook pour récupérer le statut du bot
 */
export const useBotStatus = (options: { enabled?: boolean } = {}) => {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['bot', 'status'],
    queryFn: () => apiClient.getBotStatus(),
    enabled,
    staleTime: 5 * 1000, // 5 secondes
    refetchInterval: 10 * 1000, // Actualiser toutes les 10 secondes
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