import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  RefreshCw, 
  Server, 
  Database, 
  Zap,
  Bot,
  Activity,
  Clock
} from 'lucide-react';
import { useApiClient } from '@/hooks/useApiClient';

interface ServiceStatus {
  name: string;
  status: 'operational' | 'degraded' | 'down' | 'maintenance';
  lastCheck: string;
  responseTime?: number;
  message?: string;
  icon: React.ReactNode;
}

interface SystemLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  service: string;
  message: string;
  details?: Record<string, any>;
}

interface ErrorLog {
  id: string;
  timestamp: string;
  service: string;
  error: string;
  stack?: string;
  resolved: boolean;
}

const ServicesMonitor: React.FC = () => {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [systemLogs, setSystemLogs] = useState<SystemLog[]>([]);
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  
  const { apiClient } = useApiClient();
  const { toast } = useToast();

  // Initialiser les services à surveiller
  const initializeServices = (): ServiceStatus[] => [
    {
      name: 'API Backend',
      status: 'operational',
      lastCheck: new Date().toISOString(),
      icon: <Server className="h-4 w-4" />
    },
    {
      name: 'Base de Données',
      status: 'operational', 
      lastCheck: new Date().toISOString(),
      icon: <Database className="h-4 w-4" />
    },
    {
      name: 'Redis Cache',
      status: 'operational',
      lastCheck: new Date().toISOString(),
      icon: <Zap className="h-4 w-4" />
    },
    {
      name: 'Bot Trading',
      status: 'operational',
      lastCheck: new Date().toISOString(),
      icon: <Bot className="h-4 w-4" />
    },
    {
      name: 'WebSocket',
      status: 'operational',
      lastCheck: new Date().toISOString(),
      icon: <Activity className="h-4 w-4" />
    }
  ];

  const checkSystemHealth = async () => {
    setIsRefreshing(true);
    const startTime = Date.now();
    
    try {
      // Vérifier l'API Backend
      const healthResponse = await fetch('/api/v1/system/health');
      const healthData = await healthResponse.json();
      const responseTime = Date.now() - startTime;
      
      // Mettre à jour les statuts des services
      const updatedServices = services.map(service => {
        switch (service.name) {
          case 'API Backend':
            return {
              ...service,
              status: healthResponse.ok ? 'operational' : 'down',
              responseTime,
              lastCheck: new Date().toISOString(),
              message: healthData.message || undefined
            };
          case 'Base de Données':
            return {
              ...service,
              status: healthData.database?.status === 'connected' ? 'operational' : 'down',
              lastCheck: new Date().toISOString(),
              message: healthData.database?.message
            };
          case 'Redis Cache':
            return {
              ...service,
              status: healthData.redis?.status === 'connected' ? 'operational' : 'down',
              lastCheck: new Date().toISOString(),
              message: healthData.redis?.message
            };
          default:
            return service;
        }
      });
      
      setServices(updatedServices);
      setLastUpdate(new Date());
      
      // Ajouter un log de système
      const newLog: SystemLog = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        level: 'info',
        service: 'Monitor',
        message: `Health check completed in ${responseTime}ms`
      };
      
      setSystemLogs(prev => [newLog, ...prev.slice(0, 49)]);
      
    } catch (error) {
      console.error('Health check failed:', error);
      
      // Marquer l'API comme down
      setServices(prev => prev.map(service => 
        service.name === 'API Backend' 
          ? { ...service, status: 'down', lastCheck: new Date().toISOString() }
          : service
      ));
      
      // Ajouter un log d'erreur
      const errorLog: ErrorLog = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        service: 'API Backend',
        error: error instanceof Error ? error.message : 'Connection failed',
        resolved: false
      };
      
      setErrorLogs(prev => [errorLog, ...prev.slice(0, 49)]);
      
      toast({
        title: "Erreur de monitoring",
        description: "Impossible de vérifier le statut des services",
        variant: "destructive"
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  // Auto-refresh toutes les 30 secondes
  useEffect(() => {
    setServices(initializeServices());
    checkSystemHealth();
    
    const interval = setInterval(checkSystemHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'operational':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'down':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'maintenance':
        return <Clock className="h-4 w-4 text-blue-500" />;
    }
  };

  const getStatusVariant = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'operational':
        return 'default';
      case 'degraded':
        return 'warning' as any;
      case 'down':
        return 'destructive';
      case 'maintenance':
        return 'secondary';
    }
  };

  const getLogLevelIcon = (level: SystemLog['level']) => {
    switch (level) {
      case 'info':
        return <CheckCircle className="h-3 w-3 text-blue-500" />;
      case 'warning':
        return <AlertTriangle className="h-3 w-3 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-3 w-3 text-red-500" />;
      case 'critical':
        return <XCircle className="h-3 w-3 text-red-700" />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-base font-medium">
          Monitoring des Services
        </CardTitle>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-muted-foreground">
            Dernière mise à jour: {lastUpdate.toLocaleTimeString('fr-FR')}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={checkSystemHealth}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-3 w-3 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs defaultValue="status" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="status">Statut Services</TabsTrigger>
            <TabsTrigger value="logs">Logs Système</TabsTrigger>
            <TabsTrigger value="errors">Erreurs</TabsTrigger>
          </TabsList>
          
          <TabsContent value="status" className="space-y-3 mt-4">
            {services.map((service) => (
              <div key={service.name} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  {service.icon}
                  <div>
                    <div className="font-medium text-sm">{service.name}</div>
                    {service.message && (
                      <div className="text-xs text-muted-foreground">{service.message}</div>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {service.responseTime && (
                    <span className="text-xs text-muted-foreground">
                      {service.responseTime}ms
                    </span>
                  )}
                  <Badge variant={getStatusVariant(service.status)} className="gap-1">
                    {getStatusIcon(service.status)}
                    {service.status === 'operational' ? 'Opérationnel' : 
                     service.status === 'degraded' ? 'Dégradé' :
                     service.status === 'down' ? 'Arrêté' : 'Maintenance'}
                  </Badge>
                </div>
              </div>
            ))}
          </TabsContent>
          
          <TabsContent value="logs" className="mt-4">
            <ScrollArea className="h-[300px]">
              <div className="space-y-2">
                {systemLogs.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    Aucun log système récent
                  </div>
                ) : (
                  systemLogs.map((log, index) => (
                    <div key={log.id}>
                      <div className="flex items-start space-x-3 p-2">
                        {getLogLevelIcon(log.level)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{log.service}</span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(log.timestamp).toLocaleTimeString('fr-FR')}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground">{log.message}</p>
                          {log.details && (
                            <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-x-auto">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                      {index < systemLogs.length - 1 && <Separator />}
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="errors" className="mt-4">
            <ScrollArea className="h-[300px]">
              <div className="space-y-2">
                {errorLogs.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
                    Aucune erreur récente détectée
                  </div>
                ) : (
                  errorLogs.map((error, index) => (
                    <div key={error.id}>
                      <Alert variant={error.resolved ? "default" : "destructive"}>
                        <XCircle className="h-4 w-4" />
                        <AlertDescription>
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">{error.service}</span>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs">
                                {new Date(error.timestamp).toLocaleString('fr-FR')}
                              </span>
                              <Badge variant={error.resolved ? "default" : "destructive"}>
                                {error.resolved ? 'Résolu' : 'Actif'}
                              </Badge>
                            </div>
                          </div>
                          <p className="text-sm">{error.error}</p>
                          {error.stack && (
                            <details className="mt-2">
                              <summary className="text-xs cursor-pointer hover:underline">
                                Voir la stack trace
                              </summary>
                              <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-x-auto">
                                {error.stack}
                              </pre>
                            </details>
                          )}
                        </AlertDescription>
                      </Alert>
                      {index < errorLogs.length - 1 && <div className="h-2" />}
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default ServicesMonitor; 