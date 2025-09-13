"""
Main entry point for the GitHub Commit Analyzer MCP Server.
"""

import sys
import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, continue without it


def main():
    """Main entry point for the MCP server."""
    # Import and run the FastMCP server
    from infrastructure.fastmcp_server import run_server
    run_server()


if __name__ == "__main__":
    main()