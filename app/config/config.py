from pathlib import Path
from typing import Tuple
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    API_V1_STR: str   
    PROJECT_NAME: str 
    SQLALCHEMY_DATABASE_URI: str
    SUPPORTED_LOCALES_STRING: str
    
    @property
    def BASE_DIR(self) -> Path:
        """Get the base directory of the application."""
        return Path(__file__).resolve().parent.parent
    
    @property
    def SUPPORTED_LOCALES(self) -> Tuple[str, ...]:
        """Get supported locales as a tuple."""
        return tuple(self.SUPPORTED_LOCALES_STRING.split(","))

    class Config:
        env_file = ".env"


settings = Settings()
