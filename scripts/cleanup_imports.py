#!/usr/bin/env python3
"""
Script de nettoyage automatique pour NumerusX
- Supprime les imports inutiles
- Identifie le code dupliqué
- Formate le code selon les standards
- Vérifie la cohérence des modèles
"""

import os
import ast
import sys
from pathlib import Path
from typing import Set, List, Dict, Tuple
import re
from collections import defaultdict

class ImportCleaner:
    def __init__(self, project_root: str):
        # Si project_root pointe déjà vers app/, l'utiliser directement
        if Path(project_root).name == "app":
            self.app_dir = Path(project_root)
            self.project_root = Path(project_root).parent
        else:
            self.project_root = Path(project_root)
            self.app_dir = self.project_root / "app"
        self.unused_imports = defaultdict(list)
        self.duplicate_code = []
        
    def analyze_file(self, file_path: Path) -> Dict:
        """Analyse un fichier Python pour identifier les problèmes."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Analyser les imports
            imports = self._extract_imports(tree)
            used_names = self._extract_used_names(tree)
            unused = self._find_unused_imports(imports, used_names)
            
            return {
                'file': file_path,
                'imports': imports,
                'used_names': used_names,
                'unused_imports': unused,
                'lines': content.split('\n'),
                'content': content
            }
            
        except Exception as e:
            print(f"Erreur lors de l'analyse de {file_path}: {e}")
            return {}
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict]:
        """Extrait tous les imports d'un AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'name': alias.asname or alias.name.split('.')[-1],
                        'line': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'type': 'from_import',
                        'module': module,
                        'name': alias.asname or alias.name,
                        'original_name': alias.name,
                        'line': node.lineno
                    })
        
        return imports
    
    def _extract_used_names(self, tree: ast.AST) -> Set[str]:
        """Extrait tous les noms utilisés dans le code."""
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Pour les attributs comme module.function
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
                    
        return used_names
    
    def _find_unused_imports(self, imports: List[Dict], used_names: Set[str]) -> List[Dict]:
        """Identifie les imports inutiles."""
        unused = []
        
        for imp in imports:
            name = imp['name']
            # Vérifications spéciales
            if name in ['logger', 'logging', 'config', 'Config']:
                continue  # Souvent utilisés indirectement
            if imp.get('original_name') == '*':
                continue  # Skip wildcard imports
            if imp['module'].startswith('__'):
                continue  # Skip dunder modules
                
            if name not in used_names:
                # Vérifier si c'est un module utilisé en notation pointée
                module_used = any(n.startswith(f"{name}.") for n in used_names)
                if not module_used:
                    unused.append(imp)
                    
        return unused
    
    def find_duplicate_functions(self, files_data: List[Dict]) -> List[Dict]:
        """Identifie les fonctions potentiellement dupliquées."""
        function_signatures = defaultdict(list)
        
        for file_data in files_data:
            if not file_data:
                continue
                
            try:
                tree = ast.parse(file_data['content'])
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Créer une signature basée sur le nom et les paramètres
                        args = [arg.arg for arg in node.args.args]
                        signature = f"{node.name}({', '.join(args)})"
                        
                        function_signatures[signature].append({
                            'file': file_data['file'],
                            'line': node.lineno,
                            'name': node.name,
                            'signature': signature
                        })
            except:
                continue
        
        # Identifier les duplicatas potentiels
        duplicates = []
        for signature, locations in function_signatures.items():
            if len(locations) > 1:
                duplicates.append({
                    'signature': signature,
                    'locations': locations,
                    'count': len(locations)
                })
        
        return duplicates
    
    def clean_unused_imports(self, file_path: Path, unused_imports: List[Dict]) -> str:
        """Supprime les imports inutiles d'un fichier."""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Marquer les lignes à supprimer
        lines_to_remove = set()
        for imp in unused_imports:
            lines_to_remove.add(imp['line'] - 1)  # ast.lineno est 1-indexed
        
        # Créer le nouveau contenu
        cleaned_lines = []
        for i, line in enumerate(lines):
            if i not in lines_to_remove:
                cleaned_lines.append(line)
            else:
                print(f"  Suppression import ligne {i+1}: {line.strip()}")
        
        return ''.join(cleaned_lines)
    
    def run_cleanup(self) -> Dict:
        """Lance le nettoyage complet du projet."""
        print("🧹 Démarrage du nettoyage du code NumerusX...")
        
        # Trouver tous les fichiers Python
        python_files = list(self.app_dir.rglob("*.py"))
        python_files = [f for f in python_files if not f.name.startswith('.')]
        
        print(f"📁 Analyse de {len(python_files)} fichiers Python...")
        
        # Analyser chaque fichier
        files_data = []
        total_unused = 0
        
        for file_path in python_files:
            print(f"🔍 Analyse: {file_path.relative_to(self.project_root)}")
            file_data = self.analyze_file(file_path)
            if file_data:
                files_data.append(file_data)
                
                unused = file_data.get('unused_imports', [])
                if unused:
                    print(f"  ⚠️  {len(unused)} imports inutiles trouvés")
                    total_unused += len(unused)
                    
                    # Option de nettoyage automatique
                    if input(f"  Nettoyer {file_path.name}? (y/N): ").lower() == 'y':
                        cleaned_content = self.clean_unused_imports(file_path, unused)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(cleaned_content)
                        print(f"  ✅ {file_path.name} nettoyé")
        
        # Chercher le code dupliqué
        print("\n🔍 Recherche de code dupliqué...")
        duplicates = self.find_duplicate_functions(files_data)
        
        if duplicates:
            print(f"⚠️  {len(duplicates)} fonctions potentiellement dupliquées trouvées:")
            for dup in duplicates[:10]:  # Limiter l'affichage
                print(f"  📋 {dup['signature']} ({dup['count']} occurrences)")
                for loc in dup['locations']:
                    rel_path = loc['file'].relative_to(self.project_root)
                    print(f"    📄 {rel_path}:{loc['line']}")
        
        # Résumé
        results = {
            'files_analyzed': len(files_data),
            'total_unused_imports': total_unused,
            'duplicate_functions': len(duplicates),
            'duplicates_detail': duplicates
        }
        
        print(f"\n📊 Résumé du nettoyage:")
        print(f"  📁 Fichiers analysés: {results['files_analyzed']}")
        print(f"  🗑️  Imports inutiles: {results['total_unused_imports']}")
        print(f"  📋 Fonctions dupliquées: {results['duplicate_functions']}")
        
        return results

class CodeQualityChecker:
    """Vérifie la qualité et la cohérence du code."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / "app"
    
    def check_model_consistency(self) -> Dict:
        """Vérifie la cohérence des modèles Pydantic."""
        print("\n🔍 Vérification de la cohérence des modèles...")
        
        model_files = [
            self.app_dir / "models" / "ai_inputs.py",
            self.app_dir / "api" / "v1" / "auth_routes.py",
            self.app_dir / "api" / "v1" / "config_routes.py",
        ]
        
        issues = []
        for file_path in model_files:
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Vérifier les imports Pydantic
                    if 'from pydantic import' in content:
                        if 'BaseModel' not in content:
                            issues.append(f"{file_path.name}: Utilise Pydantic mais pas BaseModel")
                    
                    # Vérifier la cohérence des types
                    if 'Optional[' in content and 'from typing import' not in content:
                        issues.append(f"{file_path.name}: Utilise Optional sans l'importer")
                        
                except Exception as e:
                    issues.append(f"{file_path.name}: Erreur de lecture - {e}")
        
        return {
            'issues': issues,
            'files_checked': len([f for f in model_files if f.exists()])
        }
    
    def suggest_refactoring(self) -> List[str]:
        """Suggère des améliorations de refactoring."""
        suggestions = []
        
        # Analyser la structure des routes API
        api_dir = self.app_dir / "api" / "v1"
        if api_dir.exists():
            route_files = list(api_dir.glob("*_routes.py"))
            
            # Vérifier la cohérence des patterns
            auth_patterns = []
            for route_file in route_files:
                try:
                    with open(route_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'verify_token' in content:
                        auth_patterns.append(route_file.name)
                    
                    # Vérifier les patterns de gestion d'erreur
                    if 'HTTPException' in content and 'try:' not in content:
                        suggestions.append(f"Ajouter gestion d'erreur try/catch dans {route_file.name}")
                
                except:
                    continue
            
            if len(auth_patterns) < len(route_files):
                suggestions.append("Standardiser l'authentification dans toutes les routes")
        
        # Vérifier la structure des services
        if (self.app_dir / "trading").exists():
            suggestions.append("Considérer l'extraction des services de trading en modules séparés")
        
        return suggestions

def main():
    """Point d'entrée principal du script de nettoyage."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = Path(__file__).parent.parent
    
    print("🚀 NumerusX Code Cleanup Tool")
    print("=" * 50)
    
    # Nettoyage des imports
    cleaner = ImportCleaner(project_root)
    cleanup_results = cleaner.run_cleanup()
    
    # Vérification de la qualité
    quality_checker = CodeQualityChecker(project_root)
    model_check = quality_checker.check_model_consistency()
    suggestions = quality_checker.suggest_refactoring()
    
    print(f"\n🎯 Vérification des modèles:")
    print(f"  📁 Fichiers vérifiés: {model_check['files_checked']}")
    if model_check['issues']:
        print(f"  ⚠️  Problèmes trouvés:")
        for issue in model_check['issues']:
            print(f"    • {issue}")
    else:
        print(f"  ✅ Aucun problème détecté")
    
    if suggestions:
        print(f"\n💡 Suggestions d'amélioration:")
        for suggestion in suggestions:
            print(f"  • {suggestion}")
    
    print(f"\n✨ Nettoyage terminé!")
    return cleanup_results

if __name__ == "__main__":
    main() 