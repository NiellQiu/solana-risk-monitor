import asyncio
import contextlib
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List

from app.adapters.polymarket_adapter import PolymarketAdapter
from app.adapters.solana_adapter import SolanaAdapter
from app.core.config import settings
from app.models.analysis import GainEstimate, PotentialPick, UnifiedSignal
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

    def potential_picks(
        self,
        limit: int = 20,
        min_score: int | None = None,
        min_risk_reward: float | None = None,
    ) -> List[PotentialPick]:
        min_score = min_score if min_score is not None else settings.min_pick_score
        min_risk_reward = (
            min_risk_reward if min_risk_reward is not None else settings.min_pick_risk_reward
        )
        out: List[PotentialPick] = []
        for mint, gain in self._gain_results.items():
            risk = self._risk_results.get(mint)
            if not risk:
                continue
            if risk.risk_level == "high" or risk.score < min_score:
                continue
            if gain.expected_value_pct <= 0:
                continue
            if gain.risk_reward_ratio < min_risk_reward:
                continue
            # Strict safety gates: exclude obvious rug-pull flags.
            if risk.signals.known_scam_flag or risk.signals.connected_holders_flag:
                continue
            if risk.signals.liquidity_locked is False:
                continue
            if risk.signals.mint_authority_disabled is False:
                continue
            if risk.signals.freeze_authority_disabled is False:
                continue
            if (
                risk.signals.top10_holder_pct is not None
                and risk.signals.top10_holder_pct > settings.max_top10_holder_pct
            ):
                continue
            out.append(
                PotentialPick(
                    mint=mint,
                    symbol=gain.symbol,
                    score=risk.score,
                    risk_level=risk.risk_level,
                    expected_value_pct=gain.expected_value_pct,
                    estimated_upside_pct=gain.estimated_upside_pct,
                    estimated_downside_pct=gain.estimated_downside_pct,
                    risk_reward_ratio=gain.risk_reward_ratio,
                    confidence=gain.confidence,
                    summary="; ".join(risk.reasons[:2]),
                    updated_at=risk.updated_at,
                )
            )
        return sorted(
            out,
            key=lambda item: (item.expected_value_pct, item.risk_reward_ratio, item.score),
            reverse=True,
        )[:limit]

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
