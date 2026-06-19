# This file will loads our application's configuration from environment variables (.env)
# Such as secret keys for tokens, API keys, Database adresses etc.

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# Inherits from BaseSettings which comes from pydantic_settings
class Settings(BaseSettings):
    model_config = SettingsConfigDict( # Automatically load values from .env file
        env_file = ".env", # .env file stores sensitive configurations (data that shouldn't go in Source Control)
        env_file_encoding="utf-8",
    )

    secret_key: SecretStr # SecretStr is a speacial type that won't be leak the value in logs or print out
    algorithm: str = "HS256" # If it gets out accidentally, it will be hashed by HS256 algorithm
    access_token_expire_minutes: int = 30 # Every token will automatically expire in 30 minutes

settings = Settings() # Loaded from .env file

# How does pydantic settings knows which environment variable maps to which of these fields?
# Field names match to environment variable names and they're case insensitive.
# For example secret_key will be mapped to all upper case SECRET_KEY value in .env file

# Everything in our .env file will be plain text but pydantic settings will handle these type conversions
# .env will overwrite by config.py which means if we already decided the values in both .env and config.py files
# The system will use the config.py file values even if they're different.
# If config.py does not have any values, it will use .env values and if niether of them hasn't, pydantic settings will use the default values.