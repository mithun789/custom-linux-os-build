#!/usr/bin/env python3
"""
MCP Server for Testing & Validation
Usage: python3 testing_mcp.py
"""
import subprocess
import os
from fastmcp import FastMCP

mcp = FastMCP("testing-server")

@mcp.tool()
async def validate_build() -> dict:
    """Validate build artifacts."""
    artifacts = os.path.expanduser("~/buildroot/output/images")
    
    try:
        results = {}
        
        # Check kernel
        kernel = os.path.join(artifacts, "zImage")
        if os.path.exists(kernel):
            size = os.path.getsize(kernel) / (1024*1024)
            results["kernel"] = f"✓ Found ({size:.2f} MB)"
        else:
            results["kernel"] = "✗ Not found"
        
        # Check rootfs
        rootfs = os.path.join(artifacts, "rootfs.ext4")
        if os.path.exists(rootfs):
            size = os.path.getsize(rootfs) / (1024*1024)
            results["rootfs"] = f"✓ Found ({size:.2f} MB)"
        else:
            results["rootfs"] = "✗ Not found"
        
        return results
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def run_checksums() -> str:
    """Generate checksums of artifacts."""
    artifacts = os.path.expanduser("~/buildroot/output/images")
    os.chdir(artifacts)
    
    try:
        result = subprocess.run(
            ["sha256sum", "*"],
            capture_output=True,
            text=True,
            shell=True
        )
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def check_artifact_sizes() -> dict:
    """Check if artifacts meet size requirements."""
    artifacts = os.path.expanduser("~/buildroot/output/images")
    
    try:
        sizes = {}
        total = 0
        
        for f in os.listdir(artifacts):
            fpath = os.path.join(artifacts, f)
            if os.path.isfile(fpath):
                size_mb = os.path.getsize(fpath) / (1024*1024)
                sizes[f] = size_mb
                total += size_mb
        
        return {
            "artifacts": sizes,
            "total_mb": total,
            "kernel_ok": sizes.get("zImage", 0) < 50,
            "rootfs_ok": sizes.get("rootfs.ext4", 0) < 1000
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def test_boot_image() -> dict:
    """Verify boot image integrity."""
    artifacts = os.path.expanduser("~/buildroot/output/images")
    
    try:
        checks = {
            "boot_loader": False,
            "kernel": False,
            "rootfs": False,
            "all_ok": False
        }
        
        # Check bootloader
        if os.path.exists(os.path.join(artifacts, "u-boot.bin")):
            checks["boot_loader"] = True
        elif os.path.exists(os.path.join(artifacts, "bzImage")):
            checks["boot_loader"] = True  # Alternative bootloader
        
        # Check kernel
        if os.path.exists(os.path.join(artifacts, "zImage")) or os.path.exists(os.path.join(artifacts, "bzImage")):
            checks["kernel"] = True
        
        # Check rootfs
        if os.path.exists(os.path.join(artifacts, "rootfs.ext4")):
            checks["rootfs"] = True
        
        checks["all_ok"] = checks["kernel"] and checks["rootfs"]
        
        return checks
    except Exception as e:
        return {"error": str(e)}

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
