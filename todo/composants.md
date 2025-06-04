# Documentation complète des composants shadcn/ui

Cette documentation exhaustive répertorie tous les composants disponibles dans la bibliothèque shadcn/ui, organisée pour permettre à une IA intégrée dans un IDE de recommander le composant approprié selon le contexte et les besoins du développeur.

## Composants d'interface utilisateur principaux

### Composants de base

**Accordion** - Ensemble de titres interactifs empilés verticalement révélant chacun une section de contenu. Utilisation typique : FAQ, sections de contenu pliables, organisation de documentation, navigation latérale avec sections extensibles. Propriétés principales : `type` (single/multiple), `collapsible`, `defaultValue`, support d'orientation. Conforme WAI-ARIA, construit sur les primitives Radix UI.

**Alert** - Affiche un message d'alerte pour attirer l'attention de l'utilisateur avec icône, titre et description optionnels. Usage : messages d'erreur, notifications de succès, avertissements, messages informatifs. Options : `variant` (default/destructive), support d'icônes personnalisées, titre et description. Peut inclure des boutons d'action.

**Alert Dialog** - Dialogue modal qui interrompt l'utilisateur avec du contenu important nécessitant une réponse. Cas d'usage : dialogues de confirmation, avertissements d'actions destructives, messages système critiques. Composants : trigger, contenu, en-tête, pied de page, description. Rend le contenu sous-jacent inerte, axé sur l'accessibilité.

**Avatar** - Élément image avec fallback pour représenter les utilisateurs ou entités. Utilisation : photos de profil utilisateur, affichage de membres d'équipe, listes de contacts, sections de commentaires. Options : source d'image, texte/initiales de fallback, variantes de taille, formes personnalisées. Fallback automatique vers les initiales.

**Badge** - Petits descripteurs de statut pour les éléments d'interface. Usage : indicateurs de statut, étiquettes, libellés, compteurs, marqueurs de catégorie. Propriétés : `variant` (default/secondary/destructive/outline), options de taille. Peut être utilisé avec des liens via la prop asChild.

**Button** - Élément cliquable pour déclencher des actions. Utilisation : soumissions de formulaires, navigation, actions, CTA, boutons de barre d'outils. Options : `variant` (default/secondary/destructive/outline/ghost/link), `size` (default/sm/lg/icon), `asChild` pour les liens. Support des états de chargement, icônes, états désactivés.

**Card** - Conteneur flexible avec sections d'en-tête, contenu et pied de page. Usage : conteneurs de contenu, cartes de produits, widgets de tableau de bord, aperçus d'articles. Composants : header, content, footer, description, title, action. Hautement composable.

## Composants de formulaires et de saisie

**Calendar** - Composant de sélection de date avec navigation. Utilisation : sélecteurs de date, interfaces de planification, systèmes de réservation, planificateurs d'événements. Options : modes de sélection simple/multiple/plage, dates désactivées, formatage personnalisé. Construit sur React DayPicker.

**Checkbox** - Entrée binaire pour les sélections et états booléens. Usage : sélections de formulaire, actions en masse, commutateurs de paramètres, sélection d'éléments de liste. Propriétés : états coché/non coché/indéterminé, option désactivée. Support de l'état indéterminé.

**Input** - Champ de saisie texte pour l'entrée de données utilisateur. Utilisation : formulaires, champs de recherche, saisie de données, authentification utilisateur. Options : types d'entrée multiples (text/email/password/file), placeholder, états désactivés. Support des libellés et validation.

**Input OTP** - Saisie de mot de passe à usage unique avec plusieurs emplacements. Usage : authentification à deux facteurs, codes de vérification, saisies de sécurité. Propriétés : nombre d'emplacements configurable, motifs personnalisés, séparateurs. Fonctionnalité copier-coller, navigation clavier.

**Label** - Libellés accessibles pour les entrées de formulaire. Usage : libellés de champs de formulaire, descriptions d'entrée, améliorations d'accessibilité. S'associe avec les contrôles de formulaire, essentiel pour l'accessibilité des lecteurs d'écran.

**Radio Group** - Ensemble d'options mutuellement exclusives. Utilisation : sélections à choix unique, options de paramètres, questions d'enquête. Options : orientation (vertical/horizontal), valeurs par défaut, options désactivées. Une seule sélection autorisée par groupe.

**Select** - Composant de sélection déroulante. Usage : sélection d'options, menus déroulants de formulaire, interfaces de filtrage, paramètres. Propriétés : sélection simple, regroupement, contenu défilable, déclencheurs personnalisés. Support de la navigation clavier.

**Switch** - Commutateur à bascule pour les choix binaires. Utilisation : commutateurs de paramètres, commutateurs de fonctionnalités, préférences booléennes. Options : états coché/non coché, option désactivée. Alternative à la checkbox pour les états on/off.

**Textarea** - Saisie de texte multi-ligne. Usage : commentaires, messages, descriptions, saisie de contenu long. Propriétés : placeholder, états désactivés, redimensionnement automatique, limites de caractères. Support de l'intégration et validation de formulaires.

## Navigation et mise en page

**Breadcrumb** - Navigation hiérarchique montrant l'emplacement actuel. Usage : navigation de site web, navigation de système de fichiers, processus multi-étapes. Options : séparateurs personnalisés, points de suspension pour chemins longs, support déroulant. Design responsif avec éléments pliables.

**Menubar** - Barre de menu persistante pour applications de style bureau. Utilisation : menus d'application, interfaces d'applications de bureau, systèmes de navigation complexes. Propriétés : menus imbriqués, raccourcis clavier, éléments radio/checkbox, séparateurs. Similaire aux barres de menu d'applications de bureau.

**Navigation Menu** - Collection de liens de navigation avec support déroulant. Usage : en-têtes de site web, navigation principale, systèmes de menus complexes. Options : navigation multi-niveau, déclencheurs personnalisés, design responsif. Support de structures de navigation imbriquées complexes.

**Pagination** - Navigation pour contenu paginé. Utilisation : navigation de table, résultats de recherche, articles de blog, listes de données. Propriétés : numéros de page, boutons précédent/suivant, options de taille de page. Gère les grands ensembles de données avec points de suspension.

**Sidebar** - Composant de barre latérale composable avec navigation. Usage : navigation de tableau de bord, barres latérales d'applications, interfaces d'administration, documentation. Options : pliable, en-têtes/pieds de page, sections de menu, comportement responsif. Hautement personnalisable.

## Affichage et retour d'information

**Aspect Ratio** - Conteneur qui maintient un rapport largeur-hauteur spécifique. Usage : intégrations vidéo, conteneurs d'image, médias responsifs, mises en page de cartes. Propriétés : ratio configurable (16:9, 4:3, 1:1, etc.). Utile pour maintenir des mises en page cohérentes.

**Progress** - Indicateur visuel de progression de tâche. Utilisation : états de chargement, téléchargements de fichiers, achèvement de formulaire, indicateurs d'étapes. Options : états déterminé/indéterminé, style personnalisé, plages de valeurs. Accessible avec attributs ARIA appropriés.

**Skeleton** - Animation de placeholder pour contenu en chargement. Usage : états de chargement, placeholders de contenu, amélioration de performance perçue. Propriétés : formes et tailles variées, contrôles d'animation. Améliore l'expérience utilisateur pendant le chargement.

**Sonner (Toast)** - Système de notification toast moderne. Utilisation : messages de succès, notifications d'erreur, confirmations d'action, alertes système. Options : variantes multiples, boutons d'action, positionnement, rejet automatique. Remplace le composant Toast déprécié.

## Composants interactifs

**Collapsible** - Composant qui étend/réduit les panneaux de contenu. Usage : sections FAQ, panneaux d'informations détaillées, zones de contenu extensibles. Propriétés : états ouvert/fermé, déclencheurs personnalisés, contrôles d'animation. Excellent pour gérer l'espace et la divulgation progressive.

**Command** - Palette de commandes avec recherche et navigation clavier. Utilisation : commandes d'application, interfaces de recherche, actions rapides, raccourcis clavier. Options : fonctionnalité de recherche, regroupement, raccourcis clavier, états vides. Souvent utilisé avec des dialogues.

**Combobox** - Combinaison d'entrée et de menu déroulant pour l'autocomplétion. Usage : recherche avec suggestions, champs d'autocomplétion, sélections filtrées. Propriétés : filtrage de recherche, options personnalisées, navigation clavier. Construit avec les composants Popover et Command.

**Context Menu** - Menu contextuel de clic droit avec actions. Utilisation : actions de clic droit, opérations contextuelles, actions secondaires. Options : menus imbriqués, séparateurs, raccourcis, éléments radio/checkbox. Fonctionnalité de clic droit de style bureau.

**Dialog** - Fenêtre modale superposée au contenu principal. Usage : formulaires, confirmations, vues détaillées, contenu modal. Propriétés : déclencheurs personnalisés, en-têtes, pieds de page, contrôles de fermeture. Rend le contenu sous-jacent inerte.

**Drawer** - Panneau coulissant depuis le bord de l'écran. Utilisation : navigation mobile, panneaux latéraux, panneaux de paramètres, filtres. Options : direction de glissement (haut/droite/bas/gauche), tailles personnalisées. Excellent pour les interfaces mobiles.

**Dropdown Menu** - Menu déclenché par bouton avec divers types d'actions. Usage : menus d'action, menus utilisateur, sélecteurs d'options, actions contextuelles. Propriétés : menus imbriqués, checkboxes, groupes radio, séparateurs, raccourcis. Très polyvalent.

**Hover Card** - Popover qui apparaît au survol pour informations supplémentaires. Usage : aperçus d'utilisateur, informations supplémentaires, tooltips avec contenu riche. Options : déclencheurs de survol, positionnement personnalisé, support de contenu riche. Bon pour la divulgation progressive.

**Popover** - Panneau flottant pour contenu riche. Utilisation : informations supplémentaires, aides de formulaire, tooltips riches, contenu secondaire. Propriétés : positionnement personnalisé, déclencheurs, support de contenu riche. Plus flexible que les tooltips de base.

**Sheet** - Extension de dialogue qui glisse depuis le bord de l'écran. Usage : formulaires de barre latérale, navigation mobile, panneaux de paramètres, tiroirs de contenu. Options : positionnement latéral (haut/droite/bas/gauche), tailles personnalisées. Étend le composant Dialog.

**Tooltip** - Petit popup montrant des informations sur un élément. Utilisation : texte d'aide, explications, contexte supplémentaire, améliorations d'accessibilité. Propriétés : positionnement, délais, contenu personnalisé. Essentiel pour l'accessibilité.

## Composants spécialisés

**Carousel** - Composant pour afficher plusieurs éléments avec navigation. Usage : galeries d'images, vitrines de produits, témoignages, mises en avant de fonctionnalités. Options : lecture automatique, boucle infinie, orientation, gestes de glissement. Construit sur Embla Carousel.

**Chart** - Composants de visualisation de données. Utilisation : tableaux de bord, analyses, présentation de données, rapports. Propriétés : types de graphiques multiples, thématisation, design responsif. Construit pour les besoins de visualisation de données.

**Data Table** - Table avancée avec tri, filtrage et pagination. Usage : interfaces d'administration, gestion de données, rapports, grands ensembles de données. Options : construit avec TanStack Table, tri, filtrage, pagination, sélection de lignes. Solution de table hautement personnalisable.

**Date Picker** - Composant d'entrée pour sélection de date. Utilisation : formulaires nécessitant des dates, planification, systèmes de réservation, filtrage. Propriétés : plages de dates, dates désactivées, formatage personnalisé, validation. Combine Calendar avec Input dans un Popover.

**Resizable** - Composants pour créer des mises en page de panneaux redimensionnables. Usage : mises en page à volets partagés, personnalisation de tableau de bord, interfaces de style IDE. Options : orientation horizontale/verticale, tailles minimales, poignées de redimensionnement. Excellent pour les mises en page personnalisables par l'utilisateur.

**Scroll-area** - Zone défilable personnalisée avec barres de défilement stylées. Usage : contenu défilable personnalisé, style de défilement cohérent, longues listes. Propriétés : style de barre de défilement personnalisé, défilement horizontal/vertical. Expérience de défilement cohérente entre navigateurs.

**Separator** - Diviseur visuel entre sections de contenu. Usage : séparation de contenu, organisation visuelle, structure de mise en page. Options : orientation horizontale/verticale, style personnalisé. Simple mais essentiel pour la hiérarchie visuelle.

**Slider** - Composant d'entrée pour sélectionner des valeurs dans une plage. Utilisation : paramètres avec plages, filtres, contrôles de volume, plages de prix. Propriétés : valeurs simples/multiples, incréments d'étapes, sélection de plage. Alternative d'entrée de plage accessible.

**Table** - Composant de table de base pour données tabulaires. Usage : affichage de données simples, tables de comparaison, contenu structuré. Propriétés : sections légende, en-tête, corps, pied de page. Fondation pour des tables de données plus complexes.

**Tabs** - Sections de contenu en couches avec navigation par onglets. Utilisation : panneaux de paramètres, interfaces multi-vues, contenu catégorisé. Options : orientation horizontale, sélection par défaut, déclencheurs personnalisés. Excellent pour organiser le contenu connexe.

**Toggle** - Bouton à deux états (on/off). Usage : boutons de barre d'outils, contrôles de formatage, options binaires. Propriétés : états pressé/non pressé, variantes, tailles. Différent de Switch - utilisé pour des actions plutôt que des paramètres.

**Toggle Group** - Ensemble de boutons de bascule pour sélection multiple ou simple. Usage : barres d'outils de formatage, contrôles de filtre, groupes d'options. Options : sélection simple/multiple, variantes, orientation. Bon pour les options de bascule connexes.

## Intégration de formulaires

**Form (React Hook Form)** - Gestion complète de formulaires avec validation. Usage : formulaires complexes, validation, gestion d'état de formulaire, saisie utilisateur. Propriétés : construit avec react-hook-form, validation de schéma Zod, composants de champ. Solution de formulaire complète avec validation et gestion d'erreurs intégrées.

## Directives de sélection pour l'intégration d'IA IDE

**Pour les formulaires** : Input, Label, Button, Select, Checkbox, Radio Group, Switch, Textarea, Calendar, Date Picker, Form

**Pour la navigation** : Breadcrumb, Navigation Menu, Menubar, Sidebar, Pagination, Tabs

**Pour les retours** : Alert, Toast (Sonner), Progress, Skeleton, Tooltip

**Pour l'affichage de données** : Table, Data Table, Card, Badge, Avatar, Chart

**Pour les superpositions** : Dialog, Sheet, Popover, Hover Card, Drawer, Context Menu, Dropdown Menu

**Pour la mise en page** : Aspect Ratio, Separator, Resizable, Scroll-area, Collapsible

**Pour les éléments interactifs** : Button, Toggle, Toggle Group, Slider, Command, Combobox

**Pour l'organisation du contenu** : Accordion, Carousel, Tabs, Card

Chaque composant est conçu pour être accessible, personnalisable et fonctionner de manière transparente avec d'autres composants shadcn/ui tout en maintenant des modèles de conception cohérents. L'installation se fait via CLI avec `pnpm dlx shadcn@latest add [nom-du-composant]`, et tous les composants sont construits sur des primitives Radix UI pour l'accessibilité, stylés avec Tailwind CSS, et incluent le support TypeScript.