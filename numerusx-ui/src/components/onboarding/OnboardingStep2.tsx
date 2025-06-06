import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Palette, Monitor, Smartphone, Languages, Eye, CheckCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface OnboardingStep2Props {
  data: any;
  onChange: (data: any) => void;
}

interface ThemePalette {
  name: string;
  displayName: string;
  description: string;
  primaryColor: string;
  preview: string[];
}

const OnboardingStep2: React.FC<OnboardingStep2Props> = ({ data, onChange }) => {
  const [selectedPalette, setSelectedPalette] = useState(data.theme_palette || 'slate');
  const [selectedTheme, setSelectedTheme] = useState(data.theme_name || 'default');
  const [selectedLanguage, setSelectedLanguage] = useState(data.language || 'en');

  // Theme palettes from shadcn/ui
  const themePalettes: ThemePalette[] = [
    {
      name: 'slate',
      displayName: 'Slate',
      description: 'Gris frais avec des nuances bleues',
      primaryColor: '#334155',
      preview: ['#f8fafc', '#e2e8f0', '#cbd5e1', '#94a3b8', '#64748b']
    },
    {
      name: 'gray',
      displayName: 'Gray',
      description: 'Gris neutre classique',
      primaryColor: '#374151',
      preview: ['#f9fafb', '#e5e7eb', '#d1d5db', '#9ca3af', '#6b7280']
    },
    {
      name: 'zinc',
      displayName: 'Zinc',
      description: 'Gris chaud et moderne',
      primaryColor: '#3f3f46',
      preview: ['#fafafa', '#e4e4e7', '#d4d4d8', '#a1a1aa', '#71717a']
    },
    {
      name: 'neutral',
      displayName: 'Neutral',
      description: 'Gris pur et minimaliste',
      primaryColor: '#404040',
      preview: ['#fafafa', '#e5e5e5', '#d4d4d4', '#a3a3a3', '#737373']
    },
    {
      name: 'stone',
      displayName: 'Stone',
      description: 'Gris beige chaleureux',
      primaryColor: '#44403c',
      preview: ['#fafaf9', '#e7e5e4', '#d6d3d1', '#a8a29e', '#78716c']
    }
  ];

  const themeStyles = [
    {
      name: 'default',
      displayName: 'Default',
      description: 'Style par défaut avec des bordures arrondies',
      preview: '🎨 Moderne'
    },
    {
      name: 'new-york',
      displayName: 'New York',
      description: 'Style épuré avec des lignes droites',
      preview: '📐 Minimaliste'
    }
  ];

  const languages = [
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'fr', name: 'Français', flag: '🇫🇷' },
    { code: 'es', name: 'Español', flag: '🇪🇸' },
    { code: 'de', name: 'Deutsch', flag: '🇩🇪' }
  ];

  useEffect(() => {
    const newData = {
      ...data,
      theme_palette: selectedPalette,
      theme_name: selectedTheme,
      language: selectedLanguage
    };
    onChange(newData);
  }, [selectedPalette, selectedTheme, selectedLanguage]);

  const PalettePreview: React.FC<{ palette: ThemePalette }> = ({ palette }) => (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium">{palette.displayName}</div>
          <div className="text-sm text-muted-foreground">{palette.description}</div>
        </div>
        {selectedPalette === palette.name && (
          <CheckCircle className="h-5 w-5 text-green-500" />
        )}
      </div>
      
      {/* Color swatches */}
      <div className="flex space-x-1">
        {palette.preview.map((color, index) => (
          <div
            key={index}
            className="w-8 h-8 rounded-md border-2 border-border"
            style={{ backgroundColor: color }}
          />
        ))}
      </div>
      
      {/* Sample UI elements */}
      <div className="p-3 border rounded-lg space-y-2" style={{ borderColor: palette.preview[2] }}>
        <div className="flex items-center justify-between">
          <div className="h-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full w-16"></div>
          <div className="text-xs text-muted-foreground">Aperçu</div>
        </div>
        <div className="h-1 rounded" style={{ backgroundColor: palette.preview[3] }}></div>
        <div className="h-1 rounded w-3/4" style={{ backgroundColor: palette.preview[4] }}></div>
      </div>
    </div>
  );

  const ThemeStylePreview: React.FC<{ theme: any }> = ({ theme }) => (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium">{theme.displayName}</div>
          <div className="text-sm text-muted-foreground">{theme.description}</div>
        </div>
        <div className="text-lg">{theme.preview}</div>
      </div>
      
      {/* Style preview */}
      <div className={`p-3 border space-y-2 ${
        theme.name === 'default' ? 'rounded-lg' : 'rounded-none'
      }`}>
        <div className={`h-8 bg-primary/10 flex items-center px-3 ${
          theme.name === 'default' ? 'rounded-md' : 'rounded-none'
        }`}>
          <div className="text-sm">Élément UI</div>
        </div>
        <div className="flex space-x-2">
          <div className={`h-6 w-16 bg-muted ${
            theme.name === 'default' ? 'rounded' : 'rounded-none'
          }`}></div>
          <div className={`h-6 w-12 bg-muted ${
            theme.name === 'default' ? 'rounded' : 'rounded-none'
          }`}></div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <Alert>
        <Palette className="h-4 w-4" />
        <AlertDescription>
          Personnalisez l'apparence de votre interface. Vous pourrez modifier ces paramètres à tout moment dans les réglages.
        </AlertDescription>
      </Alert>

      {/* Color Palette Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Palette className="h-5 w-5" />
            <span>Palette de Couleurs</span>
          </CardTitle>
          <CardDescription>
            Choisissez une palette de couleurs basée sur les thèmes shadcn/ui
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup value={selectedPalette} onValueChange={setSelectedPalette}>
            <div className="grid gap-4">
              {themePalettes.map((palette) => (
                <div key={palette.name} className="flex items-start space-x-3">
                  <RadioGroupItem 
                    value={palette.name} 
                    id={palette.name}
                    className="mt-4"
                  />
                  <Label htmlFor={palette.name} className="flex-1 cursor-pointer">
                    <Card className={`transition-all duration-200 ${
                      selectedPalette === palette.name 
                        ? 'ring-2 ring-primary shadow-md' 
                        : 'hover:shadow-sm'
                    }`}>
                      <CardContent className="p-4">
                        <PalettePreview palette={palette} />
                      </CardContent>
                    </Card>
                  </Label>
                </div>
              ))}
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      {/* Theme Style Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Monitor className="h-5 w-5" />
            <span>Style de Thème</span>
          </CardTitle>
          <CardDescription>
            Sélectionnez le style général de l'interface
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup value={selectedTheme} onValueChange={setSelectedTheme}>
            <div className="grid gap-4">
              {themeStyles.map((theme) => (
                <div key={theme.name} className="flex items-start space-x-3">
                  <RadioGroupItem 
                    value={theme.name} 
                    id={`theme-${theme.name}`}
                    className="mt-4"
                  />
                  <Label htmlFor={`theme-${theme.name}`} className="flex-1 cursor-pointer">
                    <Card className={`transition-all duration-200 ${
                      selectedTheme === theme.name 
                        ? 'ring-2 ring-primary shadow-md' 
                        : 'hover:shadow-sm'
                    }`}>
                      <CardContent className="p-4">
                        <ThemeStylePreview theme={theme} />
                      </CardContent>
                    </Card>
                  </Label>
                </div>
              ))}
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      {/* Language Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Languages className="h-5 w-5" />
            <span>Langue de l'Interface</span>
          </CardTitle>
          <CardDescription>
            Choisissez la langue pour l'interface utilisateur
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Sélectionner une langue" />
            </SelectTrigger>
            <SelectContent>
              {languages.map((lang) => (
                <SelectItem key={lang.code} value={lang.code}>
                  <div className="flex items-center space-x-2">
                    <span>{lang.flag}</span>
                    <span>{lang.name}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Preview Summary */}
      <Card className="bg-muted/50">
        <CardHeader>
          <CardTitle className="text-base flex items-center space-x-2">
            <Eye className="h-4 w-4" />
            <span>Aperçu de votre Configuration</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium">Palette:</span>
              <div className="mt-1">
                <Badge variant="outline">
                  {themePalettes.find(p => p.name === selectedPalette)?.displayName}
                </Badge>
              </div>
            </div>
            <div>
              <span className="font-medium">Style:</span>
              <div className="mt-1">
                <Badge variant="outline">
                  {themeStyles.find(t => t.name === selectedTheme)?.displayName}
                </Badge>
              </div>
            </div>
            <div>
              <span className="font-medium">Langue:</span>
              <div className="mt-1">
                <Badge variant="outline">
                  {languages.find(l => l.code === selectedLanguage)?.flag}{' '}
                  {languages.find(l => l.code === selectedLanguage)?.name}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Help Text */}
      <Alert>
        <Monitor className="h-4 w-4" />
        <AlertDescription>
          <strong>Conseil:</strong> Ces paramètres affecteront l'apparence de toute l'application. 
          Vous pourrez les modifier à tout moment depuis les paramètres.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default OnboardingStep2; 