#!/usr/bin/env python3
"""
Test script to validate that all API modules can be imported correctly.
This helps identify import issues before running the full application.
"""

import sys
import os
import traceback
from typing import List, Tuple

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))


def test_import(module_name: str) -> Tuple[bool, str]:
    """Test importing a module and return success status and error message if any."""
    try:
        __import__(module_name)
        return True, f"✅ {module_name}"
    except Exception as e:
        error_msg = f"❌ {module_name}: {str(e)}"
        return False, error_msg


def main():
    """Main test function."""
    print("🔍 Testing API module imports...\n")
    
    # List of modules to test
    modules_to_test = [
        # Core modules
        "app.config",
        "app.database",
        "app.socket_manager",
        
        # API modules
        "app.api.v1",
        "app.api.v1.auth_routes",
        "app.api.v1.bot_routes",
        "app.api.v1.config_routes",
        "app.api.v1.trades_routes",
        "app.api.v1.portfolio_routes",
        "app.api.v1.ai_decisions_routes",
        "app.api.v1.system_routes",
        
        # AI and trading modules
        "app.ai_agent",
        "app.models.ai_inputs",
        "app.dex_bot",
        
        # Utility modules
        "app.utils.exceptions",
        "app.portfolio_manager",
        
        # Main application
        "app.main"
    ]
    
    successful_imports = []
    failed_imports = []
    
    for module in modules_to_test:
        success, message = test_import(module)
        print(message)
        
        if success:
            successful_imports.append(module)
        else:
            failed_imports.append((module, message))
    
    # Summary
    print(f"\n📊 Import Test Summary:")
    print(f"✅ Successful: {len(successful_imports)}")
    print(f"❌ Failed: {len(failed_imports)}")
    
    if failed_imports:
        print(f"\n🚨 Failed imports:")
        for module, error in failed_imports:
            print(f"  - {error}")
        
        print(f"\n💡 Tips to fix import errors:")
        print("  - Install missing dependencies: pip install -r requirements.txt")
        print("  - Check for syntax errors in the failing modules")
        print("  - Verify all required environment variables are set")
        print("  - Make sure you're running from the project root directory")
        
        return 1
    else:
        print(f"\n🎉 All imports successful! The API should start correctly.")
        return 0


def test_database_creation():
    """Test database creation and basic operations."""
    print(f"\n🗄️  Testing database creation...")
    
    try:
        from app.database import EnhancedDatabase
        from app.config import Config
        
        # Test with in-memory database
        db = EnhancedDatabase(db_path=":memory:")
        
        # Test AI decision recording
        decision_data = {
            "decision_type": "BUY",
            "token_pair": "SOL/USDC", 
            "confidence": 0.85,
            "reasoning": "Test decision",
            "aggregated_inputs": {"test": "data"}
        }
        
        decision_id = db.record_ai_decision(decision_data)
        if decision_id:
            print("✅ Database AI decision recording works")
        else:
            print("❌ Database AI decision recording failed")
            return False
        
        # Test AI decision retrieval
        history = db.get_ai_decision_history(limit=1)
        if len(history) == 1:
            print("✅ Database AI decision retrieval works")
        else:
            print("❌ Database AI decision retrieval failed")
            return False
        
        db.close()
        print("✅ Database operations successful")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False


def test_socket_manager():
    """Test Socket.io manager initialization."""
    print(f"\n🔌 Testing Socket.io manager...")
    
    try:
        from app.socket_manager import get_socket_manager
        
        manager = get_socket_manager()
        if manager and manager.sio:
            print("✅ Socket.io manager initialization works")
            
            # Test utility methods
            count = manager.get_authenticated_clients_count()
            print(f"✅ Socket.io client count: {count}")
            
            return True
        else:
            print("❌ Socket.io manager initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Socket.io manager test failed: {e}")
        traceback.print_exc()
        return False


def test_api_routes():
    """Test API routes can be imported and FastAPI app created."""
    print(f"\n🌐 Testing API routes...")
    
    try:
        from app.main import app
        from app.api.v1 import api_router
        
        if app and api_router:
            print("✅ FastAPI app and API router creation works")
            
            # Check that routes are registered
            routes_count = len(app.routes)
            print(f"✅ FastAPI app has {routes_count} routes registered")
            
            return True
        else:
            print("❌ FastAPI app or API router creation failed")
            return False
            
    except Exception as e:
        print(f"❌ API routes test failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 NumerusX API Import and Basic Functionality Test\n")
    
    # Test imports
    import_result = main()
    
    if import_result == 0:
        # Only run additional tests if imports are successful
        all_tests_passed = True
        
        # Test database
        if not test_database_creation():
            all_tests_passed = False
        
        # Test socket manager
        if not test_socket_manager():
            all_tests_passed = False
        
        # Test API routes
        if not test_api_routes():
            all_tests_passed = False
        
        if all_tests_passed:
            print(f"\n🎉 All tests passed! NumerusX API is ready to run.")
            print(f"\n▶️  To start the API server:")
            print(f"   uvicorn app.main:final_asgi_app --host 0.0.0.0 --port 8000 --reload")
            sys.exit(0)
        else:
            print(f"\n⚠️  Some functionality tests failed. Check the errors above.")
            sys.exit(1)
    else:
        print(f"\n❌ Import tests failed. Fix the import errors before running the API.")
        sys.exit(import_result) 