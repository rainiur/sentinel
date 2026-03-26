"""Summarize ``SENTINEL_MCP_CONFIG`` (Cursor ``mcpServers``) without exposing secrets."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

Transport = Literal["stdio", "http"]


def mcp_config_path() -> str:
    return os.getenv("SENTINEL_MCP_CONFIG", "").strip()


def summarize_mcp_servers() -> dict[str, Any]:
    """
    Return a JSON-serializable summary safe to expose in the API.

    Omits commands, args, URLs, headers, and env values.
    """
    path = mcp_config_path()
    if not path:
        return {
            "loaded": False,
            "path_configured": False,
            "error": None,
            "server_count": 0,
            "servers": [],
        }
    if not os.path.isfile(path):
        return {
            "loaded": False,
            "path_configured": True,
            "error": "file_not_found",
            "server_count": 0,
            "servers": [],
        }
    try:
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw)
    except OSError:
        return {
            "loaded": False,
            "path_configured": True,
            "error": "read_error",
            "server_count": 0,
            "servers": [],
        }
    except json.JSONDecodeError:
        return {
            "loaded": False,
            "path_configured": True,
            "error": "invalid_json",
            "server_count": 0,
            "servers": [],
        }
    if not isinstance(data, dict):
        return {
            "loaded": False,
            "path_configured": True,
            "error": "invalid_shape",
            "server_count": 0,
            "servers": [],
        }
    mcp_servers = data.get("mcpServers")
    if mcp_servers is None:
        return {
            "loaded": True,
            "path_configured": True,
            "error": None,
            "server_count": 0,
            "servers": [],
        }
    if not isinstance(mcp_servers, dict):
        return {
            "loaded": False,
            "path_configured": True,
            "error": "mcpServers_not_object",
            "server_count": 0,
            "servers": [],
        }
    servers: list[dict[str, str]] = []
    for name, spec in mcp_servers.items():
        if not isinstance(spec, dict):
            continue
        transport: Transport = "http" if spec.get("url") else "stdio"
        servers.append({"name": str(name), "transport": transport})
    servers.sort(key=lambda s: s["name"])
    return {
        "loaded": True,
        "path_configured": True,
        "error": None,
        "server_count": len(servers),
        "servers": servers,
    }
