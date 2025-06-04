# Frontend Roadmap - Vite + React + Radix UI 🎨

**Stack :** Vite + React + TypeScript + Radix UI + Tailwind CSS  
**État :** Excellente base ✅ | Composants applicatifs manquants ⚠️

## 🎯 Stack Analysis - Vous avez un excellent setup !

### ✅ **Ce qui est déjà parfait**
```bash
# Design System complet
@radix-ui/* (35+ composants installés)
tailwindcss + class-variance-authority
lucide-react (icônes cohérentes)
sonner (toasts natives)

# Fonctionnalités avancées  
react-hook-form + zod (forms robustes)
recharts (graphiques financiers)
@reduxjs/toolkit (state management)
socket.io-client (temps réel)
i18next (internationalization)
```

### 📦 **3 packages manquants seulement**
```bash
npm install @tanstack/react-table @tanstack/react-query axios
```

## 🚀 Roadmap Développement UI

### Phase 1 : Composants Applicatifs (1 semaine)

#### 1.1 Table de Trading avec TanStack Table
```typescript
// src/components/ui/data-table.tsx
import { useReactTable, getCoreRowModel } from '@tanstack/react-table'
import { Radix Table components }

export function TradingTable({ data, columns }) {
  // Implementation avec Radix Table + TanStack logic
}
```

**Features à implémenter :**
- [ ] Table trades avec pagination
- [ ] Tri et filtres par date, token, P&L
- [ ] Actions inline (view details, export)
- [ ] Responsive design mobile

#### 1.2 Dashboard KPI Cards
```typescript
// src/components/dashboard/kpi-card.tsx
import { Card, CardContent, CardHeader } from '@radix-ui/react-card'
import { TrendingUp, TrendingDown } from 'lucide-react'

export function KPICard({ title, value, change, trend }) {
  // Utiliser votre système de couleurs Tailwind
}
```

**KPIs à créer :**
- [ ] Portfolio total value (temps réel via Socket.io)
- [ ] P&L 24h avec indicateur couleur
- [ ] Nombre trades aujourd'hui
- [ ] Success rate IA Agent

#### 1.3 Graphiques Trading avec Recharts
```typescript
// src/components/charts/portfolio-chart.tsx
import { LineChart, Line, ResponsiveContainer } from 'recharts'

export function PortfolioChart({ data, timeRange }) {
  // Intégration avec votre theme Tailwind
  // Couleurs cohérentes avec Radix UI
}
```

**Graphiques prioritaires :**
- [ ] Performance portfolio temps réel
- [ ] Volume trading par jour
- [ ] Distribution des trades par token
- [ ] Historique décisions IA

### Phase 2 : Pages Fonctionnelles (1 semaine)

#### 2.1 Dashboard Principal
```typescript
// src/pages/DashboardPage.tsx (déjà créé, à compléter)
import { useQuery } from '@tanstack/react-query'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@radix-ui/react-tabs'

export default function DashboardPage() {
  // Utiliser React Query pour cache intelligent
  // Socket.io pour updates temps réel
  // Radix Tabs pour organisation
}
```

#### 2.2 Page Trading Avancée
```typescript
// src/pages/TradingPage.tsx (à enrichir)
export default function TradingPage() {
  return (
    <div className="space-y-6">
      {/* Manual trade form avec react-hook-form + zod */}
      <ManualTradeForm />
      
      {/* Tableau trades avec TanStack Table */}
      <TradingTable />
      
      {/* Graphiques prix avec Recharts */}
      <PriceCharts />
    </div>
  )
}
```

#### 2.3 Formulaires avec Validation
```typescript
// src/components/forms/manual-trade-form.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Dialog, DialogContent } from '@radix-ui/react-dialog'
import { Select, SelectContent, SelectItem } from '@radix-ui/react-select'

const tradeSchema = z.object({
  tokenAddress: z.string().min(1),
  amount: z.number().positive(),
  orderType: z.enum(['market', 'limit'])
})

export function ManualTradeForm() {
  // Votre stack form déjà parfait !
}
```

### Phase 3 : Intégrations Temps Réel (3-4 jours)

#### 3.1 Socket.io + Redux Integration
```typescript
// src/lib/socket-client.ts (utiliser votre socket.io-client)
import { io } from 'socket.io-client'
import { store } from '@/app/store'

class SocketClient {
  connect(authToken: string) {
    this.socket = io(API_URL, {
      auth: { token: authToken }
    })
    
    // Dispatch vers Redux store
    this.socket.on('portfolio_update', (data) => {
      store.dispatch(portfolioSlice.actions.updateRealtime(data))
    })
  }
}
```

#### 3.2 React Query + Auth0 Integration
```typescript
// src/lib/api-client.ts
import axios from 'axios'
import { useAuth0 } from '@auth0/auth0-react'

export function useApiClient() {
  const { getAccessTokenSilently } = useAuth0()
  
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: async () => {
      const token = await getAccessTokenSilently()
      return apiClient.get('/portfolio', {
        headers: { Authorization: `Bearer ${token}` }
      })
    }
  })
}
```

## 🎨 Design System - Votre Stack Radix UI

### Composants Disponibles (Déjà installés)
```typescript
// Layout & Navigation
import { NavigationMenu } from '@radix-ui/react-navigation-menu'
import { Collapsible } from '@radix-ui/react-collapsible'

// Data Display  
import { Table } from '@radix-ui/react-table' // Pour TanStack integration
import { Progress } from '@radix-ui/react-progress'
import { Avatar } from '@radix-ui/react-avatar'

// Forms & Input
import { Select } from '@radix-ui/react-select'
import { Slider } from '@radix-ui/react-slider'
import { Switch } from '@radix-ui/react-switch'
import { RadioGroup } from '@radix-ui/react-radio-group'

// Overlays
import { Dialog } from '@radix-ui/react-dialog'
import { Popover } from '@radix-ui/react-popover'
import { DropdownMenu } from '@radix-ui/react-dropdown-menu'
import { Toast } from '@radix-ui/react-toast' // + sonner pour facilité

// Feedback
import { AlertDialog } from '@radix-ui/react-alert-dialog'
```

### Patterns d'Usage Recommandés

#### Trading Actions
```typescript
// Confirmation trades avec AlertDialog
<AlertDialog>
  <AlertDialogTrigger asChild>
    <Button variant="destructive">Vendre Position</Button>
  </AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Confirmer Vente</AlertDialogTitle>
      <AlertDialogDescription>
        Êtes-vous sûr de vouloir vendre {amount} {tokenSymbol} ?
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Annuler</AlertDialogCancel>
      <AlertDialogAction onClick={handleSell}>Confirmer</AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

#### Settings avec Tabs
```typescript
// Page settings organisée
<Tabs defaultValue="trading" className="w-full">
  <TabsList className="grid w-full grid-cols-4">
    <TabsTrigger value="trading">Trading</TabsTrigger>
    <TabsTrigger value="risk">Risque</TabsTrigger>
    <TabsTrigger value="ai">IA Agent</TabsTrigger>
    <TabsTrigger value="notifications">Alertes</TabsTrigger>
  </TabsList>
  
  <TabsContent value="trading">
    <TradingSettingsForm />
  </TabsContent>
  {/* ... autres tabs */}
</Tabs>
```

## 🔧 Configuration Recommandée

### Tailwind Config Optimization
```javascript
// tailwind.config.js - optimisé pour trading UI
module.exports = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Trading colors
        'profit': '#10b981', // green-500
        'loss': '#ef4444',   // red-500
        'warning': '#f59e0b', // amber-500
      }
    }
  }
}
```

### Vite Config pour Performance
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'radix-ui': [/@radix-ui/],
          'recharts': ['recharts'],
          'tanstack': [/@tanstack/]
        }
      }
    }
  }
})
```

## 📋 Checklist Immédiate

### Cette Semaine
- [ ] `npm install @tanstack/react-table @tanstack/react-query axios`
- [ ] Créer TradingTable component avec Radix UI + TanStack
- [ ] Implémenter KPI cards dashboard
- [ ] Connecter Socket.io aux composants temps réel

### Semaine Suivante  
- [ ] Formulaires avancés avec validation
- [ ] Graphiques Recharts avec theme cohérent
- [ ] Integration React Query avec Auth0
- [ ] Tests composants critiques

---

**Votre stack est excellente !** Focus sur l'implémentation des composants applicatifs plutôt que sur l'installation de packages. 