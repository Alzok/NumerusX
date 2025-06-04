# 🎨 Plan d'intégration shadcn/ui pour NumerusX

## Configuration du thème

```bash
# Installation avec thème slate et couleur jaune
npx shadcn@latest init \
  --style new-york \
  --base-color slate \
  --css-variables true \
  --with-css-variables \
  --tailwind-config tailwind.config.js \
  --components src/components \
  --utils src/lib/utils
```

## 🏗️ Architecture des composants par page

### 1. **Page d'authentification** (/login)

**Composants shadcn/ui à utiliser :**
- **Card** - Conteneur principal du formulaire de login
- **Input** - Email et mot de passe
- **Label** - Étiquettes des champs
- **Button** - Boutons de connexion (Auth0)
- **Alert** - Messages d'erreur/succès
- **Separator** - Séparateur "ou continuer avec"
- **Form** - Gestion complète avec React Hook Form + Zod

```typescript
// pages/LoginPage.tsx
<Card className="w-full max-w-md mx-auto">
  <CardHeader>
    <CardTitle>Connexion NumerusX</CardTitle>
    <CardDescription>Trading bot IA pour Solana</CardDescription>
  </CardHeader>
  <CardContent>
    <Form>
      <Input type="email" />
      <Input type="password" />
      <Button variant="default" className="bg-yellow-600">
        Se connecter avec Auth0
      </Button>
    </Form>
  </CardContent>
</Card>
```

### 2. **Layout principal** (App.tsx)

**Composants shadcn/ui :**
- **Sidebar** - Navigation principale collapsible
- **Navigation Menu** - Menu horizontal pour mobile
- **Avatar** - Photo profil utilisateur
- **Dropdown Menu** - Menu utilisateur (profil, déconnexion)
- **Breadcrumb** - Navigation contextuelle
- **Separator** - Séparations visuelles
- **Sheet** - Sidebar mobile

```typescript
// Layout structure
<div className="flex h-screen bg-slate-50">
  <Sidebar className="hidden lg:block">
    <SidebarHeader>
      <Avatar /> {/* Logo NumerusX */}
    </SidebarHeader>
    <SidebarContent>
      <NavigationMenu orientation="vertical">
        {/* Dashboard, Trading, Portfolio, etc. */}
      </NavigationMenu>
    </SidebarContent>
  </Sidebar>
  
  <main className="flex-1">
    <header className="border-b">
      <Breadcrumb />
      <DropdownMenu> {/* User menu */}
        <Avatar />
      </DropdownMenu>
    </header>
    {children}
  </main>
</div>
```

### 3. **Dashboard** (/dashboard)

**Composants shadcn/ui :**
- **Card** - KPI containers
- **Chart** - Graphique portfolio (Chart.js intégré)
- **Progress** - Indicateurs de performance
- **Badge** - Statuts (Bot actif/inactif)
- **Skeleton** - Loading states
- **Tabs** - Vues différentes (24h, 7j, 30j)
- **Alert** - Notifications système
- **Sonner (Toast)** - Notifications temps réel

```typescript
// DashboardPage.tsx
<div className="grid gap-4">
  {/* KPI Cards */}
  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Portfolio</CardTitle>
        <DollarSign className="h-4 w-4 text-yellow-600" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">$15,231.89</div>
        <Progress value={65} className="mt-2" />
      </CardContent>
    </Card>
  </div>

  {/* Chart Section */}
  <Card>
    <CardHeader>
      <Tabs defaultValue="24h">
        <TabsList>
          <TabsTrigger value="24h">24h</TabsTrigger>
          <TabsTrigger value="7d">7 jours</TabsTrigger>
          <TabsTrigger value="30d">30 jours</TabsTrigger>
        </TabsList>
      </Tabs>
    </CardHeader>
    <CardContent>
      <Chart /> {/* Portfolio evolution */}
    </CardContent>
  </Card>
</div>
```

### 4. **Page Trading** (/trading)

**Composants shadcn/ui :**
- **Data Table** - Table des trades avec tri/filtrage
- **Input** - Recherche/filtres
- **Select** - Filtres par type/statut
- **Button** - Actions (Acheter/Vendre)
- **Dialog** - Formulaire de trading manuel
- **Badge** - Types de trades (BUY/SELL)
- **Toggle Group** - Sélection BUY/SELL
- **Slider** - Montant d'investissement
- **Command** - Recherche de paires

```typescript
// TradingPage.tsx
<div className="space-y-4">
  {/* Trading Form Dialog */}
  <Dialog>
    <DialogTrigger asChild>
      <Button className="bg-yellow-600">
        Nouveau Trade
      </Button>
    </DialogTrigger>
    <DialogContent>
      <Form>
        <Command> {/* Pair selection */}
          <CommandInput placeholder="Rechercher une paire..." />
        </Command>
        <ToggleGroup type="single">
          <ToggleGroupItem value="buy">Acheter</ToggleGroupItem>
          <ToggleGroupItem value="sell">Vendre</ToggleGroupItem>
        </ToggleGroup>
        <Slider /> {/* Amount */}
      </Form>
    </DialogContent>
  </Dialog>

  {/* Trades Table */}
  <Card>
    <CardHeader>
      <Input placeholder="Rechercher..." />
      <Select>
        <SelectTrigger>
          <SelectValue placeholder="Filtrer par type" />
        </SelectTrigger>
      </Select>
    </CardHeader>
    <CardContent>
      <DataTable columns={columns} data={trades} />
    </CardContent>
  </Card>
</div>
```

### 5. **Page Portfolio** (/portfolio)

**Composants shadcn/ui :**
- **Chart** - Graphiques (répartition, évolution)
- **Card** - Conteneurs de positions
- **Progress** - Barres de progression
- **Carousel** - Défilement des positions
- **Accordion** - Détails des positions
- **Hover Card** - Infos au survol
- **Aspect Ratio** - Conteneurs graphiques

```typescript
// PortfolioPage.tsx
<div className="grid gap-4">
  {/* Portfolio Charts */}
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <Card>
      <CardHeader>
        <CardTitle>Répartition</CardTitle>
      </CardHeader>
      <CardContent>
        <AspectRatio ratio={16 / 9}>
          <Chart type="pie" />
        </AspectRatio>
      </CardContent>
    </Card>
    
    <Card>
      <CardHeader>
        <CardTitle>Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <Chart type="line" />
      </CardContent>
    </Card>
  </div>

  {/* Positions Accordion */}
  <Accordion type="single" collapsible>
    {positions.map(position => (
      <AccordionItem value={position.id}>
        <AccordionTrigger>
          <HoverCard>
            {position.asset}
          </HoverCard>
        </AccordionTrigger>
        <AccordionContent>
          {/* Position details */}
        </AccordionContent>
      </AccordionItem>
    ))}
  </Accordion>
</div>
```

### 6. **Page Configuration** (/settings)

**Composants shadcn/ui :**
- **Tabs** - Sections de configuration
- **Form** - Formulaires de paramètres
- **Switch** - Options on/off
- **Select** - Listes déroulantes
- **Slider** - Paramètres numériques
- **Input** - Champs texte
- **Textarea** - Descriptions longues
- **Radio Group** - Choix exclusifs

```typescript
// SettingsPage.tsx
<Tabs defaultValue="general">
  <TabsList className="grid w-full grid-cols-4">
    <TabsTrigger value="general">Général</TabsTrigger>
    <TabsTrigger value="trading">Trading</TabsTrigger>
    <TabsTrigger value="api">API</TabsTrigger>
    <TabsTrigger value="security">Sécurité</TabsTrigger>
  </TabsList>
  
  <TabsContent value="trading">
    <Card>
      <CardContent>
        <Form>
          <div className="space-y-4">
            <div>
              <Label>Mode de trading</Label>
              <RadioGroup>
                <RadioGroupItem value="auto">Automatique</RadioGroupItem>
                <RadioGroupItem value="manual">Manuel</RadioGroupItem>
              </RadioGroup>
            </div>
            
            <div>
              <Label>Stop Loss (%)</Label>
              <Slider defaultValue={[5]} max={20} />
            </div>
            
            <div>
              <Label>Notifications</Label>
              <Switch />
            </div>
          </div>
        </Form>
      </CardContent>
    </Card>
  </TabsContent>
</Tabs>
```

## 🎯 Composants prioritaires à installer

### Phase 1 - Core UI (Immédiat)
```bash
npx shadcn@latest add button card input label form separator badge avatar
```

### Phase 2 - Layout & Navigation
```bash
npx shadcn@latest add sidebar navigation-menu breadcrumb dropdown-menu sheet tabs
```

### Phase 3 - Data Display
```bash
npx shadcn@latest add table chart progress skeleton hover-card accordion
```

### Phase 4 - Forms & Inputs
```bash
npx shadcn@latest add select switch slider radio-group toggle toggle-group command
```

### Phase 5 - Feedback & Overlays
```bash
npx shadcn@latest add alert dialog sonner tooltip popover
```

### Phase 6 - Advanced
```bash
npx shadcn@latest add carousel aspect-ratio scroll-area resizable
```

## 🎨 Configuration du thème

### tailwind.config.js
```javascript
module.exports = {
  theme: {
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
        // Ajout du jaune comme couleur accent
        accent: {
          DEFAULT: "#FFC107", // Yellow
          foreground: "#000000",
        },
      },
    },
  },
}
```

### globals.css
```css
@layer base {
  :root {
    --background: 222.2 84% 4.9%; /* Slate */
    --foreground: 210 40% 98%;
    
    --primary: 48 96% 53%; /* Yellow */
    --primary-foreground: 0 0% 0%;
    
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    
    --accent: 48 96% 53%; /* Yellow accent */
    --accent-foreground: 0 0% 0%;
  }
}
```

## 📊 Graphiques recommandés

1. **Dashboard** : Chart (line) pour évolution portfolio
2. **Portfolio** : Chart (pie) pour répartition + Chart (area) pour performance
3. **Trading** : Chart (candlestick) pour prix temps réel
4. **Analytics** : Chart (bar) pour volumes + Chart (scatter) pour corrélations

## 🚀 Commande d'installation complète

```bash
# Installation de tous les composants recommandés
npx shadcn@latest add \
  button card input label form separator badge avatar \
  sidebar navigation-menu breadcrumb dropdown-menu sheet tabs \
  table chart progress skeleton hover-card accordion \
  select switch slider radio-group toggle toggle-group command \
  alert dialog sonner tooltip popover \
  carousel aspect-ratio scroll-area resizable
```

## ✅ Avantages de cette architecture

- **Cohérence visuelle** avec le thème slate/yellow
- **Accessibilité** maximale (WAI-ARIA)
- **Performance** optimisée (lazy loading)
- **Maintenance** facilitée (composants isolés)
- **Scalabilité** pour futures fonctionnalités
- **UX moderne** et professionnelle 