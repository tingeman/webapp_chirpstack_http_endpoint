import os
from pydantic_settings import BaseSettings

# The current implementation ignores any extra settings that are not defined in the settings classes

class CommonSettings(BaseSettings):
    class Config:
        # Load the environment file based on APP_ENV variable
        env_file = f".env.{os.getenv('APP_ENV', 'development')}"
        extra = "ignore"  # Ignore extra settings

class RunServerSettings(CommonSettings):
    # Flask application settings
    HOST: str = "0.0.0.0"
    PORT: int = 8050

class ConfigSettings(CommonSettings):
    # Database settings
    DB_FILE: str = "events.sqlite"

    # JSON output directory
    JSON_OUTPUT_DIR: str = "./data/json/"

    # Any other settings can be added here
    LOG_LEVEL: str = "INFO"

# Create singleton instances of the settings to be used across the app
run_server_settings = RunServerSettings()
settings = ConfigSettings()