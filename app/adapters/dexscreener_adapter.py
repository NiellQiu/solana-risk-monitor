"""DexScreener public API (no API key). Respect 60 req/min — use small batches + poll interval."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import httpx

from app.adapters.http_client import build_client
from app.core.config import settings
from app.models.types import TokenCandidate


def _base_url() -> str:
    return settings.dexscreener_base.rstrip("/")


async def fetch_latest_solana_mints(limit: int = 40) -> List[str]:
    url = f"{_base_url()}/token-profiles/latest/v1"
    async with build_client() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
    if not isinstance(data, list):
        return []
    out: List[str] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        if str(row.get("chainId", "")).lower() != "solana":
            continue
        addr = row.get("tokenAddress") or row.get("token_address")
        if addr:
            out.append(str(addr))
        if len(out) >= limit:
            break
    return out


def _pick_best_pair(pairs: List[dict]) -> dict | None:
    """Pick the pair with highest USD liquidity."""
    valid = [p for p in pairs if isinstance(p, dict)]
    if not valid:
        return None
    return max(valid, key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0))


def _pair_to_candidate(mint: str, pair: dict) -> TokenCandidate:
    base = pair.get("baseToken") or {}
    symbol = str(base.get("symbol") or "UNKNOWN")
    symbol = symbol.encode("ascii", "replace").decode("ascii")[:32] or "UNKNOWN"
    vol = pair.get("volume") or {}
    price_change = pair.get("priceChange") or {}
    liquidity = pair.get("liquidity") or {}
    m5 = float(vol.get("m5") or 0.0)
    h1 = float(vol.get("h1") or 0.0)
    volume_15m_usd = m5 * 3.0 if m5 else h1 / 4.0
    pair_created = pair.get("pairCreatedAt")
    age_minutes = None
    if pair_created:
        try:
            age_ms = max(0.0, datetime.utcnow().timestamp() * 1000 - float(pair_created))
            age_minutes = age_ms / 60000.0
        except (TypeError, ValueError):
            pass

    return TokenCandidate(
        mint=mint,
        symbol=symbol[:32],
        age_minutes=age_minutes,
        liquidity_usd=float(liquidity.get("usd") or 0.0),
        volume_5m_usd=m5,
        market_cap_usd=float(pair.get("marketCap") or pair.get("fdv") or 0.0),
        price_change_1h_pct=float(price_change.get("h1") or 0.0),
        volume_15m_usd=volume_15m_usd,
    )


async def fetch_token_candidates(mints: List[str]) -> List[TokenCandidate]:
    if not mints:
        return []
    out: List[TokenCandidate] = []
    chunk_size = settings.dexscreener_chunk_size
    async with build_client() as client:
        for i in range(0, len(mints), chunk_size):
            chunk = mints[i : i + chunk_size]
            path = ",".join(chunk)
            url = f"{_base_url()}/tokens/v1/solana/{path}"
            response = await client.get(url)
            if response.status_code >= 400:
                continue
            payload = response.json()
            if not isinstance(payload, list):
                continue
            by_mint: Dict[str, List[dict]] = {}
            for pair in payload:
                if not isinstance(pair, dict):
                    continue
                b = str(pair.get("baseToken", {}).get("address", ""))
                if b:
                    by_mint.setdefault(b, []).append(pair)
            for mint in chunk:
                pairs = by_mint.get(mint, [])
                best = _pick_best_pair(pairs)
                if best:
                    out.append(_pair_to_candidate(mint, best))
    return out


async def discover_candidates_dexscreener(limit: int = 25) -> List[TokenCandidate]:
    mints = await fetch_latest_solana_mints(limit=limit * 2)
    if not mints:
        return []
    mints = mints[:limit]
    return await fetch_token_candidates(mints)
