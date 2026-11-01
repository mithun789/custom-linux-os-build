#!/usr/bin/env python3
"""
MCP Server for Buildroot Configuration
Usage: python3 buildroot_mcp.py
"""
import subprocess
import os
import json
from fastmcp import FastMCP

mcp = FastMCP("buildroot-server")

@mcp.tool()
async def configure_buildroot(config_options: dict) -> str:
    """Configure Buildroot with custom options.
    
    Args:
        config_options: dict with keys like:
        - BR2_ARCH: arm, x86_64, aarch64
        - BR2_PACKAGE_OPENSSH: y/n
        - BR2_PACKAGE_BUSYBOX: y/n
    """
    buildroot_path = os.path.expanduser("~/buildroot")
    config_path = os.path.join(buildroot_path, ".config")
    
    try:
        # Create minimal .config
        with open(config_path, 'w') as f:
            f.write("BR2_DEFCONFIG=\"arch/configs/defconfig\"\n")
            for key, value in config_options.items():
                if value == "y" or value == "n":
                    f.write(f"{key}={value}\n")
                else:
                    f.write(f"{key}=\"{value}\"\n")
        
        # Validate configuration
        os.chdir(buildroot_path)
        result = subprocess.run(
            ["make", "oldconfig"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return f"Configuration saved. Output:\n{result.stdout}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def get_buildroot_status() -> str:
    """Get current Buildroot configuration status."""
    buildroot_path = os.path.expanduser("~/buildroot")
    config_path = os.path.join(buildroot_path, ".config")
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = f.read()
        return f"Current config:\n{config[:500]}..."  # First 500 chars
    return "No .config found"

@mcp.tool()
async def list_available_packages() -> str:
    """List available Buildroot packages."""
    buildroot_path = os.path.expanduser("~/buildroot")
    os.chdir(buildroot_path)
    
    try:
        result = subprocess.run(
            ["make", "list-defconfigs"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout[:2000]
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
