# AI Agent package
# This makes the ai_agent directory a Python package

# Import AIAgent from the parent ai_agent module
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

__all__ = ['AIAgent'] 