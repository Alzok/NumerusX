import React from 'react';
import { Moon, Sun, Bot } from 'lucide-react'; // Example icons
import { Button } from '@/components/ui/button'; // Assuming ShadCN/UI button is installed and aliased
// import { useTheme } from 'next-themes'; // Will be used later for theme toggle

const Header: React.FC = () => {
  // const { theme, setTheme } = useTheme(); // For theme toggle

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 hidden md:flex">
          <a className="mr-6 flex items-center space-x-2" href="/">
            <Bot className="h-6 w-6" />
            <span className="hidden font-bold sm:inline-block">
              NumerusX
            </span>
          </a>
          {/* <nav className="flex items-center space-x-6 text-sm font-medium">
            <a
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              href="/dashboard"
            >
              Dashboard
            </a>
            <a
              className="transition-colors hover:text-foreground/80 text-foreground/60"
              href="/settings"
            >
              Settings
            </a>
          </nav> */}
        </div>
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          {/* Placeholder for theme toggle and user menu */}
          <nav className="flex items-center">
            {/* <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              aria-label="Toggle theme"
            >
              <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            </Button> */}
            {/* Placeholder for UserNav component (login/profile dropdown) */}
             <Button variant="outline" size="sm">Login (Placeholder)</Button>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header; 