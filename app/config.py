from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    at_username: str = "sandbox"
    at_api_key: str = ""
    at_shortcode: str = "*384*1234#"
    at_sender_id: str = "FahariLedger"

    database_url: str = "postgresql://fahari:fahari@localhost:5432/fahari_ledger"

    asr_provider: str = "whisper"
    asr_api_key: str = ""

    overstock_hour_threshold: int = 15  # 24h clock, e.g. 15 = 3pm
    overstock_stock_ratio: float = 0.4  # nudge if > 40% of morning stock unsold by the hour above

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
