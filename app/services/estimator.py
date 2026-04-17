from datetime import datetime

from app.models.analysis import GainEstimate
from app.models.types import RiskResult, TokenCandidate


def estimate_gain_profile(candidate: TokenCandidate, risk: RiskResult) -> GainEstimate:
    momentum = min(1.0, (candidate.volume_5m_usd or 0.0) / 150000.0)
    liquidity_factor = min(1.0, (candidate.liquidity_usd or 0.0) / 250000.0)
    trust_factor = risk.score / 100.0

    estimated_upside = round((18 * momentum + 14 * liquidity_factor + 12 * trust_factor), 2)
    estimated_downside = round((35 * (1 - trust_factor)) + (18 * (1 - liquidity_factor)), 2)
    expected_value = round((estimated_upside * trust_factor) - (estimated_downside * (1 - trust_factor)), 2)

    if trust_factor >= 0.75:
        confidence = "high"
    elif trust_factor >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    reasons = [
        f"Risk score contribution: {risk.score}/100.",
        f"Liquidity input: {candidate.liquidity_usd or 0:.0f} USD.",
        f"5-minute volume input: {candidate.volume_5m_usd or 0:.0f} USD.",
        "Estimate is scenario-based and not a trade guarantee.",
    ]

    return GainEstimate(
        mint=candidate.mint,
        symbol=candidate.symbol,
        confidence=confidence,
        estimated_upside_pct=estimated_upside,
        estimated_downside_pct=estimated_downside,
        expected_value_pct=expected_value,
        reasons=reasons,
        generated_at=datetime.utcnow(),
    )
