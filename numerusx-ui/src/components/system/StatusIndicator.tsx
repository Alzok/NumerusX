import React, { useState, useEffect, useCallback } from 'react';
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from "@/components/ui/popover";
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  TestTube, 
  Zap, 
  Info,
  Settings,
  RefreshCw
} from "lucide-react";
import { useOnboarding, SystemStatus } from '@/hooks/useOnboarding';

interface StatusIndicatorProps {
  className?: string;
  compact?: boolean;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ className = "", compact = false }) => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { getSystemStatus, updateOperatingMode, isLoading } = useOnboarding();

  const fetchStatus = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const status = await getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    } finally {
      setIsRefreshing(false);
    }
  }, [getSystemStatus]);

  useEffect(() => {
    fetchStatus();
    
    // Set up periodic refresh
    const interval = setInterval(fetchStatus, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const getStatusConfig = (status: SystemStatus) => {
    switch (status.status_indicator) {
      case 'operational':
        return {
          color: 'bg-green-500',
          textColor: 'text-green-700',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          icon: CheckCircle,
          label: 'Opérationnel',
          description: 'Système fonctionnel'
        };
      case 'test':
        return {
          color: 'bg-blue-500',
          textColor: 'text-blue-700',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          icon: TestTube,
          label: 'Mode Test',
          description: 'Mode simulation actif'
        };
      case 'error':
        return {
          color: 'bg-red-500',
          textColor: 'text-red-700',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          icon: XCircle,
          label: 'Erreur',
          description: 'Problème détecté'
        };
      default:
        return {
          color: 'bg-gray-500',
          textColor: 'text-gray-700',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          icon: AlertTriangle,
          label: 'Inconnu',
          description: 'Statut indéterminé'
        };
    }
  };

  const handleModeToggle = async () => {
    if (!systemStatus) return;
    
    const newMode = systemStatus.operating_mode === 'test' ? 'production' : 'test';
    
    try {
      await updateOperatingMode(newMode);
      await fetchStatus(); // Refresh status after update
    } catch (error) {
      console.error('Failed to update mode:', error);
    }
  };

  if (!systemStatus) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="w-3 h-3 bg-gray-400 rounded-full animate-pulse" />
        {!compact && <span className="text-sm text-muted-foreground">Chargement...</span>}
      </div>
    );
  }

  const statusConfig = getStatusConfig(systemStatus);
  const StatusIcon = statusConfig.icon;

  if (compact) {
    return (
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="ghost" size="sm" className={`p-2 ${className}`}>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 ${statusConfig.color} rounded-full`} />
              <StatusIcon className={`h-4 w-4 ${statusConfig.textColor}`} />
            </div>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="end">
          <StatusDetails 
            systemStatus={systemStatus}
            statusConfig={statusConfig}
            onRefresh={fetchStatus}
            onModeToggle={handleModeToggle}
            isRefreshing={isRefreshing}
            isUpdating={isLoading}
          />
        </PopoverContent>
      </Popover>
    );
  }

  return (
    <Card className={`${statusConfig.bgColor} ${statusConfig.borderColor} ${className}`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 ${statusConfig.color} rounded-full`} />
            <div>
              <div className="font-medium text-sm">{statusConfig.label}</div>
              <div className="text-xs text-muted-foreground">{statusConfig.description}</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge variant={systemStatus.operating_mode === 'test' ? 'secondary' : 'destructive'}>
              {systemStatus.operating_mode === 'test' ? (
                <><TestTube className="w-3 h-3 mr-1" /> Test</>
              ) : (
                <><Zap className="w-3 h-3 mr-1" /> Prod</>
              )}
            </Badge>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchStatus}
              disabled={isRefreshing}
              className="h-8 w-8 p-0"
            >
              <RefreshCw className={`h-3 w-3 ${isRefreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

interface StatusDetailsProps {
  systemStatus: SystemStatus;
  statusConfig: any;
  onRefresh: () => void;
  onModeToggle: () => void;
  isRefreshing: boolean;
  isUpdating: boolean;
}

const StatusDetails: React.FC<StatusDetailsProps> = ({
  systemStatus,
  statusConfig,
  onRefresh,
  onModeToggle,
  isRefreshing,
  isUpdating
}) => {
  const StatusIcon = statusConfig.icon;

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-3">
        <div className={`p-2 rounded-full ${statusConfig.bgColor}`}>
          <StatusIcon className={`h-5 w-5 ${statusConfig.textColor}`} />
        </div>
        <div>
          <div className="font-medium">{statusConfig.label}</div>
          <div className="text-sm text-muted-foreground">{statusConfig.description}</div>
        </div>
      </div>

      {systemStatus.status_message && (
        <div className="p-3 bg-muted rounded-lg">
          <div className="flex items-start space-x-2">
            <Info className="h-4 w-4 mt-0.5 text-muted-foreground" />
            <p className="text-sm">{systemStatus.status_message}</p>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Mode d'opération:</span>
          <Badge variant={systemStatus.operating_mode === 'test' ? 'secondary' : 'destructive'}>
            {systemStatus.operating_mode === 'test' ? (
              <><TestTube className="w-3 h-3 mr-1" /> Mode Test</>
            ) : (
              <><Zap className="w-3 h-3 mr-1" /> Mode Production</>
            )}
          </Badge>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Thème:</span>
          <span className="capitalize">{systemStatus.theme_palette}</span>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Configuration:</span>
          <span>{systemStatus.is_configured ? 'Complète' : 'Incomplète'}</span>
        </div>

        {systemStatus.last_configuration_update && (
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Dernière maj:</span>
            <span className="text-xs">
              {new Date(systemStatus.last_configuration_update).toLocaleDateString()}
            </span>
          </div>
        )}
      </div>

      <div className="flex space-x-2 pt-2 border-t">
        <Button
          variant="outline"
          size="sm"
          onClick={onModeToggle}
          disabled={isUpdating}
          className="flex-1"
        >
          {isUpdating ? (
            <RefreshCw className="h-3 w-3 mr-2 animate-spin" />
          ) : systemStatus.operating_mode === 'test' ? (
            <Zap className="h-3 w-3 mr-2" />
          ) : (
            <TestTube className="h-3 w-3 mr-2" />
          )}
          {systemStatus.operating_mode === 'test' ? 'Passer en Prod' : 'Passer en Test'}
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onRefresh}
          disabled={isRefreshing}
          className="px-3"
        >
          <RefreshCw className={`h-3 w-3 ${isRefreshing ? 'animate-spin' : ''}`} />
        </Button>
      </div>
    </div>
  );
};

export default StatusIndicator; 