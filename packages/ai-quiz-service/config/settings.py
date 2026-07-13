from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded
    from environment variables.
    """

    GEMINI_API_KEY: str

    MODEL_NAME: str = "gemini-2.5-flash"

    TEMPERATURE: float = 0.3

    MAX_OUTPUT_TOKENS: int = 4096

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()