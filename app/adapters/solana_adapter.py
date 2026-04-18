from datetime import datetime
from typing import List

import httpx

from app.adapters import helius_rpc
from app.adapters.dexscreener_adapter import discover_candidates_dexscreener
from app.adapters.http_client import build_client
from app.core.config import settings
from app.models.types import TokenCandidate, TokenSignals


class SolanaAdapter:
    async def discover_candidates(self) -> List[TokenCandidate]:
        if settings.birdeye_api_key:
            return await self._discover_birdeye()

        try:
            candidates = await discover_candidates_dexscreener(
                limit=min(30, settings.watchlist_limit)
            )
            if candidates:
                return candidates
        except Exception:
            pass

        return [self._fallback_candidate()]

    async def _discover_birdeye(self) -> List[TokenCandidate]:
        headers = {"X-API-KEY": settings.birdeye_api_key}
        url = f"{settings.birdeye_base}/defi/tokenlist"
        async with build_client() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            payload = response.json()

        tokens = payload.get("data", {}).get("tokens", [])[:20]
        out: List[TokenCandidate] = []
        now = datetime.utcnow()
        for item in tokens:
            listed = item.get("recent_listing_time")
            age_minutes = None
            if listed:
                age_minutes = max(0.0, (now.timestamp() - listed) / 60)
            out.append(
                TokenCandidate(
                    mint=item.get("address", ""),
                    symbol=item.get("symbol", "UNKNOWN"),
                    age_minutes=age_minutes,
                    liquidity_usd=item.get("liquidity", 0.0),
                    volume_5m_usd=item.get("v5mUSD", 0.0),
                    market_cap_usd=item.get("mc", item.get("marketCap", 0.0)),
                    price_change_1h_pct=item.get("v1hChangePercent", item.get("priceChange1h", 0.0)),
                    volume_15m_usd=item.get("v15mUSD", 0.0),
                )
            )
        return [c for c in out if c.mint]

    def _fallback_candidate(self) -> TokenCandidate:
        return TokenCandidate(
            mint="So11111111111111111111111111111111111111112",
            symbol="WSOL",
            age_minutes=120.0,
            liquidity_usd=2000000.0,
            volume_5m_usd=85000.0,
            market_cap_usd=1800000.0,
            price_change_1h_pct=-42.0,
            volume_15m_usd=210000.0,
        )

    async def fetch_signals(self, mint: str) -> TokenSignals:
        if settings.birdeye_api_key:
            return await self._signals_birdeye(mint)
        return await self._signals_free_tier(mint)

    async def _signals_birdeye(self, mint: str) -> TokenSignals:
        headers = {"X-API-KEY": settings.birdeye_api_key}
        async with build_client() as client:
            token_info = await self._safe_get_json(
                client,
                f"{settings.birdeye_base}/defi/token_security?address={mint}",
                headers,
            )
            holder_info = await self._safe_get_json(
                client,
                f"{settings.solscan_base}/token/holders?tokenAddress={mint}&offset=0&limit=10",
                {},
            )
            rug_info = await self._safe_get_json(
                client,
                f"{settings.rugcheck_base}/v1/tokens/{mint}/report/summary",
                {},
            )

        top_pct = _sum_holder_pct(holder_info)
        return TokenSignals(
            mint=mint,
            mint_authority_disabled=bool(token_info.get("mintAuthorityDisabled", False)),
            freeze_authority_disabled=bool(token_info.get("freezeAuthorityDisabled", False)),
            top10_holder_pct=top_pct,
            liquidity_locked=bool(rug_info.get("lpLocked", False)),
            known_scam_flag=bool(rug_info.get("knownScam", False)),
            connected_holders_flag=bool(rug_info.get("insiderClusters", False)),
            data_sources=["birdeye", "solscan", "rugcheck"],
        )

    async def _signals_free_tier(self, mint: str) -> TokenSignals:
        mint_dis = None
        freeze_dis = None
        if settings.helius_rpc_url:
            try:
                mint_dis, freeze_dis = await helius_rpc.get_spl_mint_authorities_disabled(mint)
            except Exception:
                pass

        async with build_client() as client:
            holder_info = await self._safe_get_json(
                client,
                f"{settings.solscan_base}/token/holders?tokenAddress={mint}&offset=0&limit=10",
                {},
            )
            rug_info = await self._safe_get_json(
                client,
                f"{settings.rugcheck_base}/v1/tokens/{mint}/report/summary",
                {},
            )

        top_pct = _sum_holder_pct(holder_info)
        return TokenSignals(
            mint=mint,
            mint_authority_disabled=mint_dis,
            freeze_authority_disabled=freeze_dis,
            top10_holder_pct=top_pct,
            liquidity_locked=bool(rug_info.get("lpLocked", False)),
            known_scam_flag=bool(rug_info.get("knownScam", False)),
            connected_holders_flag=bool(rug_info.get("insiderClusters", False)),
            data_sources=["helius-rpc", "rugcheck", "solscan"],
        )

    async def _safe_get_json(
        self, client: httpx.AsyncClient, url: str, headers: dict
    ) -> dict:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code >= 400:
                return {}
            return response.json() if response.content else {}
        except Exception:
            return {}


def _sum_holder_pct(payload: dict) -> float:
    data = payload.get("data", {}).get("result", [])
    total = 0.0
    for row in data:
        try:
            total += float(row.get("percentage", 0.0))
        except (TypeError, ValueError):
            continue
    return round(total, 2)
