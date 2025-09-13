"""
Main entry point for the GitHub Commit Analyzer MCP Server.
"""

import sys
from pathlib import Path

# Add src to Python path and run the main module
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    from src.main import main
    main()
