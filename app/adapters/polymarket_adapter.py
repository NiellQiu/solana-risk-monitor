from datetime import datetime
from typing import List

from app.models.analysis import UnifiedSignal


class PolymarketAdapter:
    async def discover_markets(self) -> List[UnifiedSignal]:
        # Stubbed feed for local no-cost usage; swap with real adapter later.
        now = datetime.utcnow()
        return [
            UnifiedSignal(
                source="POLYMARKET",
                id="poly-btc-weekly-up",
                name="BTC closes week above threshold",
                score=64,
                risk_level="medium",
                summary="Decent liquidity but event resolution risk remains.",
                updated_at=now,
            )
        ]
