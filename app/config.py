import os
from pydantic_settings import BaseSettings

class RunServerSettings(BaseSettings):
    # Flask application settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8090))

    class Config:
        # Load the environment file based on APP_ENV variable
        env_file = f".env.{os.getenv('APP_ENV', 'production')}"

class ConfigSettings(BaseSettings):
    # Database settings
    DB_FILE: str = "events.sqlite"

    # JSON output directory
    JSON_OUTPUT_DIR: str = "./json_output"

    # Any other settings can be added here
    LOG_LEVEL: str = "INFO"

    class Config:
        # Load the environment file based on APP_ENV variable
        env_file = f".env.{os.getenv('APP_ENV', 'production')}"

# Create singleton instances of the settings to be used across the app
run_server_settings = RunServerSettings()
settings = ConfigSettings()
