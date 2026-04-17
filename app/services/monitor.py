import asyncio
import contextlib
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List

from app.adapters.polymarket_adapter import PolymarketAdapter
from app.adapters.solana_adapter import SolanaAdapter
from app.core.config import settings
from app.models.analysis import GainEstimate, UnifiedSignal
from app.models.types import MonitorState, RiskResult
from app.services.estimator import estimate_gain_profile
from app.services.scoring import score_token


class MonitorService:
    def __init__(self) -> None:
        self.solana = SolanaAdapter()
        self.polymarket = PolymarketAdapter()
        self._running = False
        self._task: asyncio.Task | None = None
        self._risk_results: Dict[str, RiskResult] = {}
        self._gain_results: Dict[str, GainEstimate] = {}
        self._events: Deque[dict] = deque(maxlen=500)

    def state(self) -> MonitorState:
        return MonitorState(
            running=self._running,
            poll_interval_seconds=settings.poll_interval_seconds,
            tracked_tokens=len(self._risk_results),
        )

    def risk_results(self) -> List[RiskResult]:
        return sorted(self._risk_results.values(), key=lambda item: item.score, reverse=True)

    def gain_results(self) -> List[GainEstimate]:
        return sorted(self._gain_results.values(), key=lambda item: item.expected_value_pct, reverse=True)

    async def unified_signals(self) -> List[UnifiedSignal]:
        now = datetime.utcnow()
        solana_rows = [
            UnifiedSignal(
                source="SOLANA",
                id=item.mint,
                name=item.symbol,
                score=item.score,
                risk_level=item.risk_level,
                summary="; ".join(item.reasons[:2]),
                updated_at=now,
            )
            for item in self.risk_results()
        ]
        polymarket_rows = await self.polymarket.discover_markets()
        return solana_rows + polymarket_rows

    def event_snapshot(self) -> List[dict]:
        return list(self._events)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self._poll_once()
            except Exception as exc:
                self._events.appendleft(
                    {
                        "kind": "error",
                        "time": datetime.utcnow().isoformat(),
                        "message": f"poll_failed: {exc}",
                    }
                )
            await asyncio.sleep(settings.poll_interval_seconds)

    async def _poll_once(self) -> None:
        candidates = await self.solana.discover_candidates()
        for candidate in candidates[: settings.watchlist_limit]:
            signals = await self.solana.fetch_signals(candidate.mint)
            risk = score_token(candidate, signals)
            estimate = estimate_gain_profile(candidate, risk)
            self._risk_results[candidate.mint] = risk
            self._gain_results[candidate.mint] = estimate
            self._events.appendleft(
                {
                    "kind": "tick",
                    "time": datetime.utcnow().isoformat(),
                    "mint": candidate.mint,
                    "symbol": candidate.symbol,
                    "score": risk.score,
                    "risk": risk.risk_level,
                    "ev_pct": estimate.expected_value_pct,
                }
            )
