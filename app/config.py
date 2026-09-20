from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    at_username: str = "sandbox"
    at_api_key: str = ""
    at_shortcode: str = "*384*1234#"
    at_sender_id: str = "FahariLedger"

    database_url: str = "postgresql://fahari:fahari@db:5432/fahari_ledger"

    asr_provider: str = "whisper"
    asr_api_key: str = ""
    public_base_url: str = ""

    overstock_hour_threshold: int = 15  # 24h clock, e.g. 15 = 3pm
    overstock_stock_ratio: float = 0.4  # nudge if > 40% of morning stock unsold by the hour above

    # Declared here (rather than left to app/utils/logging.py's os.environ read
    # alone) so pydantic-settings doesn't reject it as an unknown .env key —
    # BaseSettings forbids extra fields by default. extra="ignore" is added
    # as a second line of defense against the same class of bug for any
    # future .env.example addition that isn't mirrored here.
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
