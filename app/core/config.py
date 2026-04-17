import os
from pydantic import BaseModel


class Settings(BaseModel):
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "12"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
    watchlist_limit: int = int(os.getenv("WATCHLIST_LIMIT", "200"))
    rugcheck_base: str = os.getenv("RUGCHECK_BASE", "https://api.rugcheck.xyz")
    solscan_base: str = os.getenv("SOLSCAN_BASE", "https://public-api.solscan.io")
    birdeye_base: str = os.getenv("BIRDEYE_BASE", "https://public-api.birdeye.so")
    birdeye_api_key: str = os.getenv("BIRDEYE_API_KEY", "")


settings = Settings()
