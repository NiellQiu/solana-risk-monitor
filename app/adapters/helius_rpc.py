"""Helius Solana JSON-RPC helpers (read-only)."""

from typing import Any, Optional, Tuple

import httpx

from app.core.config import settings


async def rpc_call(method: str, params: Optional[list] = None) -> Any:
    if not settings.helius_rpc_url:
        raise ValueError("HELIUS_RPC_URL is not set")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or [],
    }
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        response = await client.post(settings.helius_rpc_url, json=payload)
        response.raise_for_status()
        data = response.json()
    if "error" in data:
        raise RuntimeError(str(data["error"]))
    return data.get("result")


async def get_health() -> str:
    """Returns RPC health string, usually 'ok'."""
    result = await rpc_call("getHealth")
    return str(result)


async def get_slot() -> int:
    result = await rpc_call("getSlot")
    return int(result)


async def get_spl_mint_authorities_disabled(mint: str) -> Tuple[Optional[bool], Optional[bool]]:
    """
    Returns (mint_authority_disabled, freeze_authority_disabled).
    True means authority is None (typically safer for fixed supply / no freeze).
    None if account missing or unparsed.
    """
    try:
        result = await rpc_call("getAccountInfo", [mint, {"encoding": "jsonParsed"}])
    except Exception:
        return None, None
    if not result or not result.get("value"):
        return None, None
    data = result["value"].get("data")
    if not isinstance(data, dict):
        return None, None
    parsed = data.get("parsed")
    if not isinstance(parsed, dict):
        return None, None
    info = parsed.get("info")
    if not isinstance(info, dict):
        return None, None
    mint_auth = info.get("mintAuthority")
    freeze_auth = info.get("freezeAuthority")
    return mint_auth is None, freeze_auth is None
