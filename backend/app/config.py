from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    LM_STUDIO_BASE_URL: str = "http://localhost:1234/v1"
    LM_STUDIO_API_KEY: str = "lm-studio"
    SQL_LLM_MODEL: str = "qwen2.5-3b-instruct"
    SYNTHESIS_LLM_MODEL: str = "qwen2.5-3b-instruct"  # Fallback to qwen2.5 or gemma-3n-e4b

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()