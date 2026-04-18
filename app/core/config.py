import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / "secrets" / "local.env")


class Settings(BaseModel):
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "12"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
    watchlist_limit: int = int(os.getenv("WATCHLIST_LIMIT", "200"))
    rugcheck_base: str = os.getenv("RUGCHECK_BASE", "https://api.rugcheck.xyz")
    solscan_base: str = os.getenv("SOLSCAN_BASE", "https://public-api.solscan.io")
    birdeye_base: str = os.getenv("BIRDEYE_BASE", "https://public-api.birdeye.so")
    birdeye_api_key: str = os.getenv("BIRDEYE_API_KEY", "")
    helius_rpc_url: str = os.getenv("HELIUS_RPC_URL", "").strip()
    dexscreener_base: str = os.getenv("DEXSCREENER_BASE", "https://api.dexscreener.com")
    dexscreener_chunk_size: int = int(os.getenv("DEXSCREENER_CHUNK_SIZE", "8"))
    min_pick_score: int = int(os.getenv("MIN_PICK_SCORE", "75"))
    min_pick_risk_reward: float = float(os.getenv("MIN_PICK_RISK_REWARD", "1.5"))
    max_top10_holder_pct: float = float(os.getenv("MAX_TOP10_HOLDER_PCT", "35"))
    rebound_min_mcap_usd: float = float(os.getenv("REBOUND_MIN_MCAP_USD", "200000"))
    rebound_max_mcap_usd: float = float(os.getenv("REBOUND_MAX_MCAP_USD", "3000000"))
    rebound_min_drawdown_pct: float = float(os.getenv("REBOUND_MIN_DRAWDOWN_PCT", "35"))
    rebound_max_drawdown_pct: float = float(os.getenv("REBOUND_MAX_DRAWDOWN_PCT", "70"))
    rebound_min_volume_recovery_ratio: float = float(
        os.getenv("REBOUND_MIN_VOLUME_RECOVERY_RATIO", "1.2")
    )
    rebound_confirm_cycles: int = int(os.getenv("REBOUND_CONFIRM_CYCLES", "2"))


settings = Settings()
