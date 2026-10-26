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
    # All persistent data lives in the data volume (mounted at /var/www/app/data in the
    # container). The defaults are absolute so that they do not depend on the working
    # directory. The Dockerfile sets the same values as environment variables, which take
    # precedence over the .env.<APP_ENV> file.

    # Database settings
    DB_FILE: str = "/var/www/app/data/events.sqlite"

    # JSON output directory
    JSON_OUTPUT_DIR: str = "/var/www/app/data/json/"

    # Any other settings can be added here
    LOG_LEVEL: str = "INFO"

# Create singleton instances of the settings to be used across the app
run_server_settings = RunServerSettings()
settings = ConfigSettings()