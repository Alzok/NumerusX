import React from 'react';
import { Link, useLocation } from 'react-router-dom'; // Import Link and useLocation
import { useTranslation } from 'react-i18next'; // Import useTranslation
import { ScrollArea } from '@/components/ui/scroll-area'; // Assuming ShadCN/UI
import { cn } from '@/lib/utils'; // Assuming ShadCN/UI utility
import { Button } from '@/components/ui/button';
import { LayoutDashboard, Settings, BarChart3, Zap } from 'lucide-react'; // Removed LogOut as it will be handled by auth

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {
  // Add any specific props if needed, e.g., for user roles to show/hide links
}

const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const location = useLocation(); // Hook to get current location
  const { t } = useTranslation(); // Initialize useTranslation

  const mainNavItems = [
    { href: '/dashboard', labelKey: 'sidebar.dashboard', icon: LayoutDashboard },
    { href: '/trading', labelKey: 'sidebar.tradingActivity', icon: BarChart3 },
    { href: '/command', labelKey: 'sidebar.commandCenter', icon: Zap },
    // Add more main navigation items here
  ];

  const secondaryNavItems = [
    { href: '/settings', labelKey: 'sidebar.settings', icon: Settings },
    // { href: '/logout', label: 'Logout', icon: LogOut }, // Handled by Auth provider usually
  ];

  const renderNavLink = (item: { href: string; labelKey: string; icon: React.ElementType }, index: number) => (
    <Button
      key={`${item.labelKey}-${index}`}
      variant="ghost"
      className={cn(
        'w-full justify-start mb-1',
        location.pathname === item.href && 'bg-muted hover:bg-muted text-primary' // Active link styling
      )}
      asChild // Important: This allows Button to wrap Link and inherit its behavior
    >
      <Link to={item.href}>
        <item.icon className="mr-2 h-4 w-4" />
        {t(item.labelKey)} {/* Use t function for label */}
      </Link>
    </Button>
  );

  return (
    <aside className={cn("hidden md:flex md:flex-col md:border-r bg-background", className)}>
      <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          {/* <Bot className="h-6 w-6" /> You can add Bot icon here if you have it */}
          <span>{t('generic.menu')}</span>
        </Link>
      </div>
      <ScrollArea className="flex-1 p-4">
        <nav className="grid items-start gap-1 text-sm font-medium">
          <h3 className="px-2 py-1.5 text-xs font-semibold text-muted-foreground tracking-wider">{t('sidebar.mainHeader')}</h3>
          {mainNavItems.map(renderNavLink)}
          
          <h3 className="mt-3 px-2 py-1.5 text-xs font-semibold text-muted-foreground tracking-wider">{t('sidebar.systemHeader')}</h3>
          {secondaryNavItems.map(renderNavLink)}
        </nav>
      </ScrollArea>
      <div className="mt-auto p-4 border-t">
        {/* Placeholder for user info or quick actions */}
        <p className="text-xs text-muted-foreground text-center">
          {t('generic.version')}
        </p>
      </div>
    </aside>
  );
};

export default Sidebar; 