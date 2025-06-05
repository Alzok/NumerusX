import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  Server, 
  Database, 
  Zap, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  MemoryStick,
  HardDrive,
  Wifi,
  RefreshCw
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/apiClient';

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_latency: number;
  uptime: string;
  status: 'healthy' | 'warning' | 'critical';
}

interface ServiceStatus {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  response_time: number;
  last_check: string;
  error_count: number;
}

export const SystemMonitor: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = useState(true);

  // System Health Query
  const { data: systemHealth, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['system', 'health'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/system/health');
      return response.data;
    },
    refetchInterval: autoRefresh ? 5000 : false,
  });

  // System Metrics Query
  const { data: systemMetrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['system', 'metrics'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/system/metrics');
      return response.data;
    },
    refetchInterval: autoRefresh ? 10000 : false,
  });

  // Service Status Query
  const { data: services, isLoading: servicesLoading, refetch: refetchServices } = useQuery({
    queryKey: ['system', 'services'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/system/services');
      return response.data;
    },
    refetchInterval: autoRefresh ? 15000 : false,
  });

  // Mock data for development
  const mockMetrics: SystemMetrics = systemMetrics || {
    cpu_usage: 45.2,
    memory_usage: 68.7,
    disk_usage: 32.1,
    network_latency: 12,
    uptime: '2d 14h 32m',
    status: 'healthy'
  };

  const mockServices: ServiceStatus[] = services || [
    {
      name: 'Trading Engine',
      status: 'online',
      response_time: 23,
      last_check: '30 seconds ago',
      error_count: 0
    },
    {
      name: 'AI Agent',
      status: 'online',
      response_time: 156,
      last_check: '45 seconds ago',
      error_count: 2
    },
    {
      name: 'Database',
      status: 'online',
      response_time: 8,
      last_check: '15 seconds ago',
      error_count: 0
    },
    {
      name: 'Redis Cache',
      status: 'degraded',
      response_time: 89,
      last_check: '1 minute ago',
      error_count: 5
    },
    {
      name: 'Jupiter SDK',
      status: 'offline',
      response_time: 0,
      last_check: '5 minutes ago',
      error_count: 12
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return 'text-green-600 bg-green-50';
      case 'warning':
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50';
      case 'critical':
      case 'offline':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'warning':
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'critical':
      case 'offline':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  const handleRefreshAll = () => {
    refetchHealth();
    refetchMetrics();
    refetchServices();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Server className="h-8 w-8" />
            Surveillance Système
          </h1>
          <p className="text-muted-foreground">
            Monitoring en temps réel des composants NumerusX
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'bg-green-50 border-green-200' : ''}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleRefreshAll}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualiser
          </Button>
        </div>
      </div>

      {/* System Status Alert */}
      {mockMetrics.status !== 'healthy' && (
        <Alert variant={mockMetrics.status === 'critical' ? 'destructive' : 'default'}>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {mockMetrics.status === 'critical' 
              ? 'Problème critique détecté sur le système' 
              : 'Problème mineur détecté sur le système'
            }
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Vue d'ensemble</TabsTrigger>
          <TabsTrigger value="metrics">Métriques</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* System Health Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockMetrics.cpu_usage.toFixed(1)}%</div>
                <Progress value={mockMetrics.cpu_usage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory</CardTitle>
                <MemoryStick className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockMetrics.memory_usage.toFixed(1)}%</div>
                <Progress value={mockMetrics.memory_usage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockMetrics.disk_usage.toFixed(1)}%</div>
                <Progress value={mockMetrics.disk_usage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Network</CardTitle>
                <Wifi className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockMetrics.network_latency}ms</div>
                <div className="text-xs text-muted-foreground mt-1">Latency</div>
              </CardContent>
            </Card>
          </div>

          {/* Services Status */}
          <Card>
            <CardHeader>
              <CardTitle>État des Services</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockServices.map((service, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(service.status)}
                      <div>
                        <div className="font-medium">{service.name}</div>
                        <div className="text-sm text-muted-foreground">
                          Vérifié {service.last_check}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <div className="text-sm font-medium">{service.response_time}ms</div>
                        {service.error_count > 0 && (
                          <div className="text-xs text-red-600">
                            {service.error_count} erreurs
                          </div>
                        )}
                      </div>
                      <Badge className={getStatusColor(service.status)}>
                        {service.status.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle>Métriques Détaillées</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Uptime Système</span>
                      <span className="text-sm">{mockMetrics.uptime}</span>
                    </div>
                  </div>
                </div>
                <div className="text-center text-muted-foreground">
                  Métriques détaillées à venir...
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services">
          <Card>
            <CardHeader>
              <CardTitle>Gestion des Services</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center text-muted-foreground">
                Interface de gestion des services à venir...
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>Logs Système</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center text-muted-foreground">
                Visualiseur de logs à venir...
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SystemMonitor; 
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  Server, 
  Database, 
  Zap, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  MemoryStick,
  HardDrive,
  Wifi,
  RefreshCw
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/apiClient';

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_latency: number;
  uptime: string;
  status: 'healthy' | 'warning' | 'critical';
}

interface ServiceStatus {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  response_time: number;
  last_check: string;
  error_count: number;
}

export const SystemMonitor: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = useState(true);

  // System Health Query
  const { data: systemHealth, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['system', 'health'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/system/health');
      return response.data;
    },
    refetchInterval: autoRefresh ? 5000 : false,
  });

  // System Metrics Query
  const { data: systemMetrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['system', 'metrics'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/system/metrics');
      return response.data;
    },
    refetchInterval: autoRefresh ? 10000 : false,
  });

  // Service Status Query
  const { data: services, isLoading: servicesLoading, refetch: refetchServices } = useQuery({
    queryKey: ['system', 'services'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/system/services');
      return response.data;
    },
    refetchInterval: autoRefresh ? 15000 : false,
  });

  // Mock data for development
  const mockMetrics: SystemMetrics = systemMetrics || {
    cpu_usage: 45.2,
    memory_usage: 68.7,
    disk_usage: 32.1,
    network_latency: 12,
    uptime: '2d 14h 32m',
    status: 'healthy'
  };

  const mockServices: ServiceStatus[] = services || [
    {
      name: 'Trading Engine',
      status: 'online',
      response_time: 23,
      last_check: '30 seconds ago',
      error_count: 0
    },
    {
      name: 'AI Agent',
      status: 'online',
      response_time: 156,
      last_check: '45 seconds ago',
      error_count: 2
    },
    {
      name: 'Database',
      status: 'online',
      response_time: 8,
      last_check: '15 seconds ago',
      error_count: 0
    },
    {
      name: 'Redis Cache',
      status: 'degraded',
      response_time: 89,
      last_check: '1 minute ago',
      error_count: 5
    },
    {
      name: 'Jupiter SDK',
      status: 'offline',
      response_time: 0,
      last_check: '5 minutes ago',
      error_count: 12
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return 'text-green-600 bg-green-50';
      case 'warning':
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50';
      case 'critical':
      case 'offline':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'warning':
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'critical':
      case 'offline':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  const handleRefreshAll = () => {
    refetchHealth();
    refetchMetrics();
    refetchServices();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Server className="h-8 w-8" />
            Surveillance Système
          </h1>
          <p className="text-muted-foreground">
            Monitoring en temps réel des composants NumerusX
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'bg-green-50 border-green-200' : ''}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleRefreshAll}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualiser
          </Button>
        </div>
      </div>

      {/* System Status Alert */}
      {mockMetrics.status !== 'healthy' && (
        <Alert variant={mockMetrics.status === 'critical' ? 'destructive' : 'default'}>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {mockMetrics.status === 'critical' 
              ? 'Problème critique détecté sur le système' 
              : 'Problème mineur détecté sur le système'
            }
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Vue d'ensemble</TabsTrigger>
          <TabsTrigger value="metrics">Métriques</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* System Health Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockMetrics.cpu_usage.toFixed(1)}%</div>
                <Progress value={mockMetrics.cpu_usage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory</CardTitle>
                <MemoryStick className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockMetrics.memory_usage.toFixed(1)}%</div>
                <Progress value={mockMetrics.memory_usage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockMetrics.disk_usage.toFixed(1)}%</div>
                <Progress value={mockMetrics.disk_usage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Network</CardTitle>
                <Wifi className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockMetrics.network_latency}ms</div>
                <div className="text-xs text-muted-foreground mt-1">Latency</div>
              </CardContent>
            </Card>
          </div>

          {/* Services Status */}
          <Card>
            <CardHeader>
              <CardTitle>État des Services</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockServices.map((service, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(service.status)}
                      <div>
                        <div className="font-medium">{service.name}</div>
                        <div className="text-sm text-muted-foreground">
                          Vérifié {service.last_check}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <div className="text-sm font-medium">{service.response_time}ms</div>
                        {service.error_count > 0 && (
                          <div className="text-xs text-red-600">
                            {service.error_count} erreurs
                          </div>
                        )}
                      </div>
                      <Badge className={getStatusColor(service.status)}>
                        {service.status.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle>Métriques Détaillées</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Uptime Système</span>
                      <span className="text-sm">{mockMetrics.uptime}</span>
                    </div>
                  </div>
                </div>
                <div className="text-center text-muted-foreground">
                  Métriques détaillées à venir...
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services">
          <Card>
            <CardHeader>
              <CardTitle>Gestion des Services</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center text-muted-foreground">
                Interface de gestion des services à venir...
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>Logs Système</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center text-muted-foreground">
                Visualiseur de logs à venir...
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SystemMonitor; 