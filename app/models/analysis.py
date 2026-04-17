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
    reasons: List[str]
    generated_at: datetime


class UnifiedSignal(BaseModel):
    source: Literal["SOLANA", "POLYMARKET"]
    id: str
    name: str
    score: int
    risk_level: str
    summary: str
    updated_at: datetime
