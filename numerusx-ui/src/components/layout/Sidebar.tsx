import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarFooter,
  SidebarRail,
} from '@/components/ui/sidebar';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  BarChart3,
  TrendingUp,
  Bot,
  Settings,
  LogOut,
  User,
  DollarSign,
  Activity,
  Zap,
} from 'lucide-react';
import { useBotStatus } from '@/hooks/useBot';

interface SidebarItem {
  title: string;
  icon: React.ElementType;
  url: string;
  badge?: string;
  isActive?: boolean;
  subItems?: SidebarItem[];
}

const SidebarComponent: React.FC<{ className?: string }> = ({ className }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth0();
  const { data: botStatus } = useBotStatus();

  const navigationItems: SidebarItem[] = [
    {
      title: 'Dashboard',
      icon: BarChart3,
      url: '/dashboard',
      isActive: location.pathname === '/dashboard',
    },
    {
      title: 'Trading',
      icon: TrendingUp,
      url: '/trading',
      isActive: location.pathname === '/trading',
      subItems: [
        {
          title: 'Trades Actifs',
          icon: Activity,
          url: '/trading/active',
          isActive: location.pathname === '/trading/active',
        },
        {
          title: 'Historique',
          icon: BarChart3,
          url: '/trading/history',
          isActive: location.pathname === '/trading/history',
        },
      ],
    },
    {
      title: 'Bot IA',
      icon: Bot,
      url: '/command',
      isActive: location.pathname === '/command',
      badge: botStatus?.is_running ? 'ACTIF' : 'ARRÊTÉ',
    },
    {
      title: 'Portfolio',
      icon: DollarSign,
      url: '/portfolio',
      isActive: location.pathname === '/portfolio',
    },
    {
      title: 'Paramètres',
      icon: Settings,
      url: '/settings',
      isActive: location.pathname === '/settings',
    },
  ];

  const handleNavigation = (url: string) => {
    navigate(url);
  };

  const handleLogout = () => {
    logout({ logoutParams: { returnTo: window.location.origin } });
  };

  return (
    <Sidebar className={className} variant="sidebar">
      <SidebarHeader className="border-b">
        <div className="flex items-center gap-3 px-4 py-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Zap className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold">NumerusX</span>
            <span className="text-xs text-muted-foreground">Trading Bot IA</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="flex-1 overflow-y-auto">
        <SidebarMenu>
          {navigationItems.map((item) => (
            <SidebarMenuItem key={item.url}>
              <SidebarMenuButton
                onClick={() => handleNavigation(item.url)}
                isActive={item.isActive}
                className="w-full justify-start"
              >
                <item.icon className="h-4 w-4" />
                <span>{item.title}</span>
                {item.badge && (
                  <Badge 
                    variant={item.badge === 'ACTIF' ? 'default' : 'secondary'}
                    className={`ml-auto text-xs ${
                      item.badge === 'ACTIF' 
                        ? 'bg-green-600 hover:bg-green-700' 
                        : 'bg-slate-600 hover:bg-slate-700'
                    }`}
                  >
                    {item.badge}
                  </Badge>
                )}
              </SidebarMenuButton>
              
              {item.subItems && item.subItems.length > 0 && (
                <SidebarMenuSub>
                  {item.subItems.map((subItem) => (
                    <SidebarMenuSubItem key={subItem.url}>
                      <SidebarMenuSubButton
                        onClick={() => handleNavigation(subItem.url)}
                        isActive={subItem.isActive}
                      >
                        <subItem.icon className="h-3 w-3" />
                        <span>{subItem.title}</span>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                  ))}
                </SidebarMenuSub>
              )}
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>

      <SidebarFooter className="border-t">
        <div className="p-4 space-y-4">
          {/* Bot Status */}
          {botStatus && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div 
                  className={`h-2 w-2 rounded-full ${
                    botStatus.is_running ? 'bg-green-500' : 'bg-slate-500'
                  }`} 
                />
                <span className="text-sm text-muted-foreground">
                  Bot {botStatus.is_running ? 'Actif' : 'Arrêté'}
                </span>
              </div>
            </div>
          )}

          <Separator />

          {/* User Profile */}
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarImage src={user?.picture} alt={user?.name} />
              <AvatarFallback>
                <User className="h-4 w-4" />
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.name}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
          </div>

          {/* Logout Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="w-full justify-start"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Déconnexion
          </Button>
        </div>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
};

export default SidebarComponent; 