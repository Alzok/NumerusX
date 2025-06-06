#!/usr/bin/env python3
"""
Script de migration pour NumerusX v1.0.0
Remplace automatiquement les usages de l'ancienne configuration par config_v2.py
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple


class ConfigMigrationTool:
    """Outil de migration automatique vers config_v2.py"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / "app"
        
        # Mapping des anciens patterns vers les nouveaux
        self.migration_patterns = {
            # Import statements
            'from app.config import Config': 'from app.config_v2 import get_config',
            'import app.config': 'from app.config_v2 import get_config',
            'from config import Config': 'from app.config_v2 import get_config',
            
            # Instance creation
            'Config()': 'get_config()',
            'self.config = Config()': 'self.config = get_config()',
            'config = Config()': 'config = get_config()',
            
            # Direct access patterns
            'Config.': 'get_config().',
        }
        
        # Mapping des attributs de configuration
        self.config_attribute_mapping = {
            # Application
            'APP_NAME': 'app.app_name',
            'DEBUG': 'app.debug',
            'DEV_MODE': 'app.dev_mode',
            
            # Security
            'JWT_SECRET_KEY': 'security.jwt_secret_key',
            'JWT_EXPIRATION': 'security.jwt_expiration',
            
            # Database
            'DATABASE_URL': 'database.database_url',
            'DB_PATH': 'database.db_path',
            
            # Redis
            'REDIS_URL': 'redis.url',
            'REDIS_HOST': 'redis.host',
            'REDIS_PORT': 'redis.port',
            
            # Solana
            'SOLANA_RPC_URL': 'solana.rpc_url',
            'SOLANA_NETWORK': 'solana.network',
            'WALLET_PATH': 'solana.wallet_path',
            'SOLANA_PRIVATE_KEY_BS58': 'solana.private_key_bs58',
            
            # Jupiter
            'JUPITER_API_KEY': 'jupiter.api_key',
            'JUPITER_LITE_API_HOSTNAME': 'jupiter.lite_api_hostname',
            'JUPITER_PRO_API_HOSTNAME': 'jupiter.pro_api_hostname',
            'JUPITER_DEFAULT_SLIPPAGE_BPS': 'jupiter.default_slippage_bps',
            
            # Trading
            'BASE_ASSET': 'trading.base_asset',
            'SLIPPAGE_BPS': 'trading.slippage_bps',
            'MAX_ORDER_SIZE_USD': 'trading.max_order_size_usd',
            'MIN_ORDER_VALUE_USD': 'trading.min_order_value_usd',
            
            # API
            'API_HOST': 'api.host',
            'API_PORT': 'api.port',
        }
        
        self.files_processed = 0
        self.changes_made = 0
    
    def migrate_file(self, file_path: Path) -> Dict[str, any]:
        """Migre un fichier Python vers la nouvelle configuration."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            if 'config' not in original_content.lower():
                return {'success': True, 'changes': 0, 'skipped': True}
            
            modified_content = original_content
            changes_count = 0
            
            # Phase 1: Remplacer les imports
            for old_pattern, new_pattern in self.migration_patterns.items():
                if old_pattern in modified_content:
                    modified_content = modified_content.replace(old_pattern, new_pattern)
                    changes_count += 1
            
            # Phase 2: Remplacer les accès aux attributs de configuration
            for old_attr, new_attr in self.config_attribute_mapping.items():
                # Patterns possibles : 
                # - config.OLD_ATTR
                # - self.config.OLD_ATTR  
                # - Config.OLD_ATTR
                patterns_to_replace = [
                    f'config.{old_attr}',
                    f'self.config.{old_attr}',
                    f'Config.{old_attr}',
                    f'get_config().{old_attr}',  # Au cas où déjà partiellement migré
                ]
                
                for pattern in patterns_to_replace:
                    if pattern in modified_content:
                        # Remplacer par get_config().new_attr
                        modified_content = modified_content.replace(
                            pattern, 
                            f'get_config().{new_attr}'
                        )
                        changes_count += 1
            
            # Phase 3: Nettoyer les importations redondantes
            modified_content = self._cleanup_imports(modified_content)
            
            # Sauvegarder seulement si des changements ont été faits
            if changes_count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                print(f"✅ Migré: {file_path.relative_to(self.app_dir)} ({changes_count} changements)")
            
            return {
                'success': True,
                'changes': changes_count,
                'original_size': len(original_content),
                'modified_size': len(modified_content)
            }
            
        except Exception as e:
            print(f"❌ Erreur migration {file_path}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _cleanup_imports(self, content: str) -> str:
        """Nettoie les imports redondants après migration."""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Supprimer les anciens imports maintenant inutiles
            if any(obsolete in line for obsolete in [
                'from app.config import Config',
                'import app.config',
                'from config import Config'
            ]):
                continue
            
            # Éviter les doublons d'imports de config_v2
            if 'from app.config_v2 import get_config' in line and any(
                'from app.config_v2 import get_config' in existing_line 
                for existing_line in cleaned_lines
            ):
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def migrate_project(self) -> Dict[str, any]:
        """Migre tout le projet vers la nouvelle configuration."""
        print("🚀 Migration vers config_v2.py")
        print("=" * 50)
        
        # Trouver tous les fichiers Python
        python_files = [
            f for f in self.app_dir.rglob("*.py") 
            if not f.name.startswith('.') and 'config' not in f.name.lower()
        ]
        
        results = {
            'total_files': len(python_files),
            'processed_files': 0,
            'total_changes': 0,
            'errors': [],
            'migrated_files': []
        }
        
        for file_path in python_files:
            if file_path.name in ['config.py', 'config_refactored.py', 'config_v2.py']:
                continue  # Skip config files themselves
            
            result = self.migrate_file(file_path)
            results['processed_files'] += 1
            
            if result['success']:
                if result.get('changes', 0) > 0:
                    results['total_changes'] += result['changes']
                    results['migrated_files'].append(str(file_path.relative_to(self.app_dir)))
            else:
                results['errors'].append({
                    'file': str(file_path.relative_to(self.app_dir)),
                    'error': result.get('error', 'Unknown error')
                })
        
        # Résumé
        print(f"\n📊 Résumé de la migration:")
        print(f"  📁 Fichiers traités: {results['processed_files']}")
        print(f"  🔄 Fichiers migrés: {len(results['migrated_files'])}")
        print(f"  ✏️  Total changements: {results['total_changes']}")
        print(f"  ❌ Erreurs: {len(results['errors'])}")
        
        if results['errors']:
            print(f"\n⚠️  Erreurs rencontrées:")
            for error in results['errors']:
                print(f"    • {error['file']}: {error['error']}")
        
        if results['migrated_files']:
            print(f"\n✅ Fichiers migrés avec succès:")
            for file_name in results['migrated_files'][:10]:  # Limiter l'affichage
                print(f"    • {file_name}")
            if len(results['migrated_files']) > 10:
                print(f"    ... et {len(results['migrated_files']) - 10} autres")
        
        return results
    
    def backup_old_configs(self):
        """Crée une sauvegarde des anciens fichiers de configuration."""
        backup_dir = self.project_root / "backup_configs"
        backup_dir.mkdir(exist_ok=True)
        
        configs_to_backup = ['config.py', 'config_refactored.py']
        
        for config_file in configs_to_backup:
            source = self.app_dir / config_file
            if source.exists():
                backup_path = backup_dir / f"{config_file}.backup"
                import shutil
                shutil.copy2(source, backup_path)
                print(f"📦 Sauvegardé: {config_file} -> {backup_path}")


def main():
    """Point d'entrée du script de migration."""
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent.parent
    
    migrator = ConfigMigrationTool(project_root)
    
    # Créer une sauvegarde
    migrator.backup_old_configs()
    
    # Effectuer la migration
    results = migrator.migrate_project()
    
    print(f"\n🎯 Migration terminée!")
    
    if results['total_changes'] > 0:
        print(f"🔄 Prochaines étapes recommandées:")
        print(f"  1. Tester l'application avec la nouvelle configuration")
        print(f"  2. Supprimer les anciens fichiers config.py et config_refactored.py")
        print(f"  3. Mettre à jour la documentation")
    
    return results


if __name__ == "__main__":
    main() 