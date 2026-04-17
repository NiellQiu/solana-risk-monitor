from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class GainEstimate(BaseModel):
    mint: str
    symbol: str
    confidence: Literal["low", "medium", "high"]
    estimated_upside_pct: float = Field(description="Scenario upside percent")
    estimated_downside_pct: float = Field(description="Scenario downside percent")
    expected_value_pct: float = Field(description="Weighted EV percent")
    risk_reward_ratio: float = Field(description="Upside divided by downside")
    reasons: List[str]
    generated_at: datetime


class PotentialPick(BaseModel):
    mint: str
    symbol: str
    score: int
    risk_level: str
    expected_value_pct: float
    estimated_upside_pct: float
    estimated_downside_pct: float
    risk_reward_ratio: float
    confidence: Literal["low", "medium", "high"]
    summary: str
    updated_at: datetime


class UnifiedSignal(BaseModel):
    source: Literal["SOLANA", "POLYMARKET"]
    id: str
    name: str
    score: int
    risk_level: str
    summary: str
    updated_at: datetime
