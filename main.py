import logging
import os
import random
import subprocess
import json
import sys
import time
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('mcp_nuclei_server')

# Create server
mcp = FastMCP("mcp_nuclei_server",
    version="1.0.0"
)

# reconfigure UnicodeEncodeError prone default (i.e. windows-1252) to utf-8
if sys.platform == "win32" and os.environ.get('PYTHONIOENCODING') is None:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

nuclei_bin_path = os.environ.get("NUCLEI_BIN_PATH")
if not nuclei_bin_path:
    logger.debug("NUCLEI_BIN_PATH is not set！")
    nuclei_bin_path = 'nuclei'
else:
    logger.info(f"nuclei_bin_path was loaded:{nuclei_bin_path}")

@mcp.tool()
def nuclei_scan_start(
    target: str,
    templates: Optional[List[str]] = None,
    severity: Optional[str] = None,
    template_tags: Optional[List[str]] = None,
    output_format: str = "json",
) -> str:
    """a mcp server for Nuclei security scan."""
    return run_nuclei(target, templates, severity,template_tags, output_format)

def run_nuclei(
    target: str,
    templates: Optional[List[str]] = None,
    severity: Optional[str] = None,
    template_tags: Optional[List[str]] = None,
    output_format: str = "json",
) -> str:
    """Run a Nuclei security scan on the specified target.
    
    Args:
        target: The target URL or IP to scan
        templates: List of specific template names to use (optional)
        template_tags: List of specific template tags names to use (optional)
        severity: Filter by severity level (critical, high, medium, low, info)
        output_format: Output format (json, text)
    
    Returns:
        str: JSON string containing scan results
    """
    try:
        # /Users/huimingliao/Documents/tools
        # Build the command
        cmd = [nuclei_bin_path, "-u", target, "-j","-duc"]
        
        # Add template filters if specified
        if templates:
            cmd.extend(["-t", ",".join(templates)])
        
        if template_tags:
            cmd.extend(["-tags", ",".join(template_tags)])
        
        # Add severity filter if specified
        if severity:
            cmd.extend(["-s", severity])
        start_time = time.time()
        # Run the scan
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output
        try:
            # 逐行解析 JSON 输出
            vulnerabilities = []
            for line in result.stdout.splitlines():
                try:
                    if line.strip():
                        vulnerability = json.loads(line)
                        vulnerabilities.append(vulnerability)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")
            return json.dumps({
                "success": True,
                "target": target,
                "time_cost_seconds": time.time() - start_time,
                "results": vulnerabilities
            })
        except json.JSONDecodeError:
            return json.dumps({
                "success": False,
                "error": "Failed to parse JSON output",
                "raw_output": result.stdout,
                "stderr": result.stderr
            })
        
        
    except subprocess.CalledProcessError as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "stderr": e.stderr
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })

if __name__ == "__main__":
    logger.info("Starting nuclei MCP server...")
    # init and run
    mcp.run(transport='stdio')