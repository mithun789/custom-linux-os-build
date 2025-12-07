#!/usr/bin/env python3
"""
MCP Server for Build Execution
Usage: python3 build_mcp.py
"""
import subprocess
import os
import time
from fastmcp import FastMCP

mcp = FastMCP("build-server")

@mcp.tool()
async def execute_build(target: str = "all", jobs: int = 4) -> dict:
    """Execute Buildroot build process.
    
    Args:
        target: 'all', 'kernel', 'rootfs', 'clean'
        jobs: number of parallel jobs
    """
    buildroot_path = os.path.expanduser("~/buildroot")
    os.chdir(buildroot_path)
    
    try:
        cmd = ["make", target, f"-j{jobs}"]
        print(f"Starting build: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        elapsed = time.time() - start_time
        
        return {
            "success": result.returncode == 0,
            "target": target,
            "duration_seconds": elapsed,
            "output": result.stdout[-1000:],  # Last 1000 chars
            "errors": result.stderr[-500:] if result.stderr else "None"
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Build timeout (>1 hour)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def list_build_artifacts() -> dict:
    """List generated OS artifacts."""
    artifacts_path = os.path.expanduser("~/buildroot/output/images")
    
    try:
        if os.path.exists(artifacts_path):
            files = os.listdir(artifacts_path)
            details = {}
            for f in files:
                fpath = os.path.join(artifacts_path, f)
                size_mb = os.path.getsize(fpath) / (1024*1024)
                details[f] = f"{size_mb:.2f} MB"
            return {"artifacts": details}
        return {"artifacts": {}, "error": "Output directory not found"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_build_status() -> dict:
    """Get current build status."""
    buildroot_path = os.path.expanduser("~/buildroot")
    os.chdir(buildroot_path)
    
    try:
        # Check if build is in progress
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        is_building = "make" in result.stdout
        
        return {
            "is_building": is_building,
            "buildroot_path": buildroot_path,
            "config_exists": os.path.exists(os.path.join(buildroot_path, ".config"))
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def clean_build() -> dict:
    """Clean previous build artifacts."""
    buildroot_path = os.path.expanduser("~/buildroot")
    os.chdir(buildroot_path)
    
    try:
        result = subprocess.run(
            ["make", "clean"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "success": result.returncode == 0,
            "message": "Build cleaned successfully" if result.returncode == 0 else "Clean failed"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
