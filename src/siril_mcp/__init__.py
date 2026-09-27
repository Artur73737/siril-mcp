"""Shared constants and paths for Siril MCP."""

from __future__ import annotations

import os
import socket
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = PACKAGE_ROOT / "catalog" / "commands.json"

SUPPORT_DIR = Path(
    os.environ.get(
        "SIRIL_MCP_SUPPORT_DIR",
        Path.home() / "Library" / "Application Support" / "siril-mcp",
    )
)
SOCKET_PATH = Path(
    os.environ.get("SIRIL_MCP_SOCKET", str(SUPPORT_DIR / "bridge.sock"))
)
STATUS_PATH = SUPPORT_DIR / "bridge.status.json"
PREVIEW_DIR = SUPPORT_DIR / "previews"

DEFAULT_PREVIEW_MAX_EDGE = 1024
PROTOCOL_VERSION = 1

# Transport: "unix" or "tcp". Auto-select TCP when AF_UNIX is unavailable
# (standard Windows Python builds). Override with SIRIL_MCP_TRANSPORT.
_HAS_AF_UNIX = hasattr(socket, "AF_UNIX")
TRANSPORT = os.environ.get("SIRIL_MCP_TRANSPORT", "unix" if _HAS_AF_UNIX else "tcp").lower()
TCP_HOST = os.environ.get("SIRIL_MCP_HOST", "127.0.0.1")
TCP_PORT = int(os.environ.get("SIRIL_MCP_PORT", "27777"))

BRIDGE_DOWN_HINT = (
    "Siril MCP bridge is not running. In Siril, run: "
    "pyscript -async <path-to-siril-mcp>/bridge/bridge.py "
    "(or use Scripts -> Start MCP Bridge after installing the helper)."
)
