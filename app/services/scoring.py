from datetime import datetime
from typing import List

from app.models.types import RiskResult, TokenCandidate, TokenSignals


def score_token(candidate: TokenCandidate, signals: TokenSignals) -> RiskResult:
    score = 100
    reasons: List[str] = []

    if signals.known_scam_flag:
        score -= 55
        reasons.append("Known scam flag detected.")
    if signals.mint_authority_disabled is False:
        score -= 20
        reasons.append("Mint authority still enabled.")
    if signals.freeze_authority_disabled is False:
        score -= 15
        reasons.append("Freeze authority still enabled.")
    if signals.liquidity_locked is False:
        score -= 20
        reasons.append("Liquidity lock signal missing.")
    if signals.top10_holder_pct is not None and signals.top10_holder_pct > 45:
        score -= 18
        reasons.append("Top-10 holder concentration is high.")
    if signals.connected_holders_flag:
        score -= 22
        reasons.append("Holder clustering suggests insider wallet overlap.")
    if candidate.age_minutes is not None and candidate.age_minutes < 20:
        score -= 8
        reasons.append("Token is very new; limited behavioral history.")
    if candidate.liquidity_usd is not None and candidate.liquidity_usd < 25000:
        score -= 14
        reasons.append("Liquidity is thin; slippage/dump risk elevated.")

    score = max(1, min(100, score))
    if score >= 75:
        risk_level = "low"
    elif score >= 50:
        risk_level = "medium"
    else:
        risk_level = "high"

    if not reasons:
        reasons.append("No major risk flags detected by configured checks.")

    return RiskResult(
        mint=candidate.mint,
        symbol=candidate.symbol,
        score=score,
        risk_level=risk_level,
        reasons=reasons,
        updated_at=datetime.utcnow(),
        signals=signals,
    )
