#!/bin/sh
set -e

# Directory where the frontend app should reside inside the container
APP_DIR="/app/numerusx-ui"
PACKAGE_JSON_PATH="${APP_DIR}/package.json"

# Create .env backend if doesn't exist
if [ ! -f "/app/.env" ] && [ -f "/app/.env.example" ]; then
  cp /app/.env.example /app/.env
  echo "Created .env from .env.example"
fi

# Ensure we're in the right directory
cd $APP_DIR

# Use existing package.json or create a fallback
if [ ! -f "$PACKAGE_JSON_PATH" ]; then
  echo "Creating complete package.json for NumerusX UI..."
  echo "⚠️  Warning: Using fallback package.json. Consider using the real one from numerusx-ui/"
  cat > package.json << 'EOF'
{
  "name": "numerusx-ui",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "@auth0/auth0-react": "^2.2.4",
    "@hookform/resolvers": "^3.3.4",
    "@tanstack/react-table": "^8.11.8",
    "@tanstack/react-query": "^5.17.15",
    "axios": "^1.6.7",
    "@radix-ui/react-accordion": "^1.1.2",
    "@radix-ui/react-alert-dialog": "^1.0.5",
    "@radix-ui/react-aspect-ratio": "^1.0.3",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-checkbox": "^1.0.4",
    "@radix-ui/react-collapsible": "^1.0.3",
    "@radix-ui/react-context-menu": "^2.1.5",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-hover-card": "^1.0.7",
    "@radix-ui/react-icons": "^1.3.0",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-menubar": "^1.0.4",
    "@radix-ui/react-navigation-menu": "^1.1.4",
    "@radix-ui/react-popover": "^1.0.7",
    "@radix-ui/react-progress": "^1.0.3",
    "@radix-ui/react-radio-group": "^1.1.3",
    "@radix-ui/react-scroll-area": "^1.0.5",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-separator": "^1.0.3",
    "@radix-ui/react-slider": "^1.1.2",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-switch": "^1.0.3",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    "@radix-ui/react-toggle": "^1.0.3",
    "@radix-ui/react-toggle-group": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "@reduxjs/toolkit": "^2.2.1",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "cmdk": "^0.2.1",
    "date-fns": "^3.3.1",
    "i18next": "^23.10.0",
    "i18next-browser-languagedetector": "^7.2.0",
    "i18next-http-backend": "^2.5.0",
    "input-otp": "^1.2.4",
    "lucide-react": "^0.344.0",
    "next-themes": "^0.2.1",
    "react": "^18.2.0",
    "react-day-picker": "^8.10.0",
    "react-dom": "^18.2.0",
    "react-hook-form": "^7.51.0",
    "react-i18next": "^14.0.5",
    "react-redux": "^9.1.0",
    "react-resizable-panels": "^2.0.12",
    "react-router-dom": "^6.22.3",
    "recharts": "^2.12.2",
    "socket.io-client": "^4.7.4",
    "sonner": "^1.4.3",
    "tailwind-merge": "^2.2.1",
    "tailwindcss-animate": "^1.0.7",
    "vaul": "^0.9.0",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "tailwindcss-animate": "^1.0.7",
    "typescript": "^5.2.2",
    "vite": "^5.0.8"
  }
}
EOF
fi

echo "Found/Created project at $APP_DIR"

# Check if node_modules exists and if package-lock.json is newer than node_modules
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ] || [ "package-lock.json" -nt "node_modules" ]; then
  echo "Installing dependencies... This may take a few minutes."
  
  # Clean install to ensure all dependencies are properly installed
  rm -rf node_modules package-lock.json
  npm cache clean --force
  
  # Install all dependencies from package.json
  npm install --legacy-peer-deps
  
  echo "Dependencies installed successfully!"

  # Installer shadcn/ui automatiquement après npm install
  echo "🎨 Installation de shadcn/ui..."
  
  # Créer components.json pour shadcn/ui avec thème slate/yellow
  cat > components.json << 'EOF'
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
EOF

  # Configurer le thème slate avec couleur jaune
  echo "🎨 Configuration du thème slate/yellow..."
  cat > src/styles/theme.css << 'EOF'
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    
    --primary: 48 96% 53%; /* Yellow */
    --primary-foreground: 0 0% 0%;
    
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    
    --accent: 48 96% 53%; /* Yellow accent */
    --accent-foreground: 0 0% 0%;
    
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    
    --ring: 48 96% 53%; /* Yellow ring */
    
    --radius: 0.5rem;
  }
  
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    
    --primary: 48 96% 53%; /* Yellow */
    --primary-foreground: 0 0% 0%;
    
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    
    --accent: 48 96% 53%; /* Yellow accent */
    --accent-foreground: 0 0% 0%;
    
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 85.7% 97.3%;
    
    --ring: 48 96% 53%; /* Yellow ring */
  }
}
EOF

  # Installer shadcn/ui CLI et composants essentiels
  npx shadcn@latest init --yes --defaults || echo "⚠️ shadcn init failed but continuing..."
  
  # Installer les composants essentiels un par un pour éviter les erreurs
  echo "📦 Installation des composants shadcn/ui..."
  npx shadcn@latest add button --yes || echo "Button component failed"
  npx shadcn@latest add input --yes || echo "Input component failed"
  npx shadcn@latest add label --yes || echo "Label component failed"
  npx shadcn@latest add card --yes || echo "Card component failed"
  npx shadcn@latest add table --yes || echo "Table component failed"
  npx shadcn@latest add badge --yes || echo "Badge component failed"
  npx shadcn@latest add dialog --yes || echo "Dialog component failed"
  npx shadcn@latest add sheet --yes || echo "Sheet component failed"
  npx shadcn@latest add sidebar --yes || echo "Sidebar component failed"
  npx shadcn@latest add breadcrumb --yes || echo "Breadcrumb component failed"
  npx shadcn@latest add separator --yes || echo "Separator component failed"
  
  echo "✅ shadcn/ui installation completed!"
  
else
  echo "Dependencies are up to date."
fi

# Verify critical dependencies are installed
echo "Verifying critical dependencies..."
MISSING_DEPS=""

# Check for critical dependencies
for dep in "react" "react-dom" "react-router-dom" "socket.io-client" "@reduxjs/toolkit" "react-redux" "vite" "@tanstack/react-table" "@tanstack/react-query" "axios" "@auth0/auth0-react"; do
  if [ ! -d "node_modules/$dep" ]; then
    MISSING_DEPS="$MISSING_DEPS $dep"
  fi
done

if [ ! -z "$MISSING_DEPS" ]; then
  echo "WARNING: Missing critical dependencies:$MISSING_DEPS"
  echo "Attempting to install missing dependencies..."
  npm install --legacy-peer-deps
fi

# Create required directories if they don't exist
mkdir -p src/components/ui
mkdir -p src/components/layout
mkdir -p src/components/charts
mkdir -p src/components/auth
mkdir -p src/features/Portfolio/components
mkdir -p src/hooks
mkdir -p src/lib
mkdir -p src/pages
mkdir -p src/assets
mkdir -p src/app
mkdir -p src/services
mkdir -p public/locales/en
mkdir -p public/locales/fr

# Create basic i18n files
if [ ! -f "public/locales/en/translation.json" ]; then
  echo '{"welcome": "Welcome to NumerusX", "dashboard": "Dashboard", "portfolio": "Portfolio", "trades": "Trades", "settings": "Settings"}' > public/locales/en/translation.json
fi

if [ ! -f "public/locales/fr/translation.json" ]; then
  echo '{"welcome": "Bienvenue sur NumerusX", "dashboard": "Tableau de bord", "portfolio": "Portefeuille", "trades": "Transactions", "settings": "Paramètres"}' > public/locales/fr/translation.json
fi

# Create basic main.tsx if it doesn't exist
if [ ! -f "src/main.tsx" ]; then
  echo "Creating src/main.tsx..."
  cat > src/main.tsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOF
fi

# Create basic App.tsx if it doesn't exist
if [ ! -f "src/App.tsx" ]; then
  echo "Creating src/App.tsx..."
  cat > src/App.tsx << 'EOF'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Provider } from 'react-redux'
import { store } from './app/store'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import Trades from './pages/Trades'
import Settings from './pages/Settings'
import Login from './pages/Login'

function App() {
  return (
    <Provider store={store}>
      <Router>
        <div className="min-h-screen bg-background">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="portfolio" element={<Portfolio />} />
              <Route path="trades" element={<Trades />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </div>
      </Router>
    </Provider>
  )
}

export default App
EOF
fi

# Create basic index.css if it doesn't exist
if [ ! -f "src/index.css" ]; then
  echo "Creating src/index.css..."
  cat > src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
EOF
fi

# Create basic Redux store if it doesn't exist
if [ ! -f "src/app/store.ts" ]; then
  echo "Creating src/app/store.ts..."
  cat > src/app/store.ts << 'EOF'
import { configureStore } from '@reduxjs/toolkit'

export const store = configureStore({
  reducer: {
    // Add your reducers here
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
EOF
fi

# Create placeholder pages if they don't exist
for page in "Dashboard" "Portfolio" "Trades" "Settings" "Login"; do
  if [ ! -f "src/pages/${page}.tsx" ]; then
    echo "Creating src/pages/${page}.tsx..."
    cat > "src/pages/${page}.tsx" << EOF
export default function ${page}() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">${page}</h1>
      <p>This is the ${page} page. Content will be added soon.</p>
    </div>
  )
}
EOF
  fi
done

# Create basic Layout component if it doesn't exist
if [ ! -f "src/components/layout/Layout.tsx" ]; then
  echo "Creating src/components/layout/Layout.tsx..."
  cat > src/components/layout/Layout.tsx << 'EOF'
import { Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="px-6 py-4">
          <h1 className="text-xl font-semibold">NumerusX</h1>
        </div>
      </header>
      <main className="container mx-auto">
        <Outlet />
      </main>
    </div>
  )
}
EOF
fi

# Ensure TypeScript config files exist
if [ ! -f "tsconfig.json" ]; then
  echo "Creating tsconfig.json..."
  cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF
fi

if [ ! -f "tsconfig.node.json" ]; then
  echo "Creating tsconfig.node.json..."
  cat > tsconfig.node.json << 'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOF
fi

# Ensure Tailwind config exists
if [ ! -f "tailwind.config.js" ]; then
  echo "Creating tailwind.config.js..."
  cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './features/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
EOF
fi

# Ensure PostCSS config exists
if [ ! -f "postcss.config.js" ]; then
  echo "Creating postcss.config.js..."
  cat > postcss.config.js << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF
fi

# Ensure Vite config exists
if [ ! -f "vite.config.ts" ]; then
  echo "Creating vite.config.ts..."
  cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true, // Listen on all addresses
    port: 5173,
    watch: {
      usePolling: true, // Use polling for file changes (needed in Docker)
    },
  },
})
EOF
fi

# Ensure index.html exists
if [ ! -f "index.html" ]; then
  echo "Creating index.html..."
  cat > index.html << 'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/logo.jpg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NumerusX - AI Trading Bot</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF
fi

# Run type checking
echo "Running TypeScript type check..."
npx tsc --noEmit || echo "TypeScript type errors found, but continuing..."

# Start the development server
echo "Starting Vite development server on port 5173..."
npm run dev -- --host 0.0.0.0
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
EOF
fi

# Ensure PostCSS config exists
if [ ! -f "postcss.config.js" ]; then
  echo "Creating postcss.config.js..."
  cat > postcss.config.js << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF
fi

# Ensure Vite config exists
if [ ! -f "vite.config.ts" ]; then
  echo "Creating vite.config.ts..."
  cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true, // Listen on all addresses
    port: 5173,
    watch: {
      usePolling: true, // Use polling for file changes (needed in Docker)
    },
  },
})
EOF
fi

# Ensure index.html exists
if [ ! -f "index.html" ]; then
  echo "Creating index.html..."
  cat > index.html << 'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/logo.jpg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NumerusX - AI Trading Bot</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF
fi

# Run type checking
echo "Running TypeScript type check..."
npx tsc --noEmit || echo "TypeScript type errors found, but continuing..."

# Start the development server
echo "Starting Vite development server on port 5173..."
npm run dev -- --host 0.0.0.0