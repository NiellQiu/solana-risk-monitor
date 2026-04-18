from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TokenCandidate(BaseModel):
    mint: str
    symbol: str = "UNKNOWN"
    age_minutes: Optional[float] = None
    liquidity_usd: Optional[float] = None
    volume_5m_usd: Optional[float] = None
    market_cap_usd: Optional[float] = None
    price_change_1h_pct: Optional[float] = None
    volume_15m_usd: Optional[float] = None


class TokenSignals(BaseModel):
    mint: str
    mint_authority_disabled: Optional[bool] = None
    freeze_authority_disabled: Optional[bool] = None
    top10_holder_pct: Optional[float] = None
    liquidity_locked: Optional[bool] = None
    known_scam_flag: Optional[bool] = None
    connected_holders_flag: Optional[bool] = None
    data_sources: List[str] = Field(default_factory=list)


class RiskResult(BaseModel):
    mint: str
    symbol: str
    score: int
    risk_level: str
    reasons: List[str]
    updated_at: datetime
    signals: TokenSignals


class MonitorState(BaseModel):
    running: bool
    poll_interval_seconds: int
    tracked_tokens: int
