from app.models.types import TokenCandidate, TokenSignals
from app.services.scoring import score_token


def test_score_flags_high_risk_token():
    candidate = TokenCandidate(mint="m1", symbol="TEST", age_minutes=4, liquidity_usd=1000, volume_5m_usd=500)
    signals = TokenSignals(
        mint="m1",
        mint_authority_disabled=False,
        freeze_authority_disabled=False,
        top10_holder_pct=78,
        liquidity_locked=False,
        known_scam_flag=True,
        connected_holders_flag=True,
    )
    result = score_token(candidate, signals)
    assert result.risk_level == "high"
    assert result.score < 50
