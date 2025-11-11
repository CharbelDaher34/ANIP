"""
Centralized configuration management using Pydantic Settings.
All services should import settings from this module instead of using os.getenv directly.
"""
from typing import Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration."""
    
    model_config = SettingsConfigDict(env_prefix='POSTGRES_', case_sensitive=False)
    
    host: str = "postgres"
    port: int = 5432
    user: str
    password: str
    db: str = "anip"
    
    @computed_field
    @property
    def url(self) -> str:
        """Construct database URL."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
    
    @computed_field
    @property
    def async_url(self) -> str:
        """Construct async database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class AirflowDatabaseSettings(BaseSettings):
    """Airflow database configuration."""
    
    model_config = SettingsConfigDict(env_prefix='AIRFLOW_DB_', case_sensitive=False)
    
    user: str = "airflow"
    password: str = "airflow"
    name: str = "airflow"
    
    @computed_field
    @property
    def url(self) -> str:
        """Construct Airflow database URL."""
        postgres_host = DatabaseSettings().host
        return f"postgresql+psycopg2://{self.user}:{self.password}@{postgres_host}:5432/{self.name}"


class MLflowSettings(BaseSettings):
    """MLflow configuration."""
    
    model_config = SettingsConfigDict(env_prefix='MLFLOW_', case_sensitive=False)
    
    tracking_uri: str = "http://mlflow:5000"
    port: int = 5000
    
    @computed_field
    @property
    def backend_store_uri(self) -> str:
        """MLflow backend store URI using PostgreSQL."""
        db = DatabaseSettings()
        return f"postgresql://{db.user}:{db.password}@{db.host}:{db.port}/{db.db}"


class SparkSettings(BaseSettings):
    """Spark configuration."""
    
    model_config = SettingsConfigDict(env_prefix='SPARK_', case_sensitive=False)
    
    master_url: str = "spark://spark-master:7077"
    master_rpc_port: int = 7077
    master_web_port: int = 8080
    worker_web_port: int = 8081
    executor_memory: str = "2g"
    driver_memory: str = "2g"
    worker_memory: str = "2g"
    worker_cores: int = 2


class NewsAPISettings(BaseSettings):
    """News API configuration."""
    
    model_config = SettingsConfigDict(case_sensitive=False)
    
    newsapi_key: Optional[str] = None
    newsdata_api_key: Optional[str] = None
    gdelt_project_id: Optional[str] = None


class AirflowSettings(BaseSettings):
    """Airflow configuration."""
    
    model_config = SettingsConfigDict(env_prefix='AIRFLOW_', case_sensitive=False)
    
    uid: int = 50000
    gid: int = 0
    admin_user: str = "admin"
    admin_password: str = "admin"
    admin_email: str = "admin@example.com"
    web_port: int = 8080


class APISettings(BaseSettings):
    """API configuration."""
    
    model_config = SettingsConfigDict(case_sensitive=False)
    
    port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = "*"


class Settings(BaseSettings):
    """
    Global application settings.
    
    Usage:
        from anip.config import settings
        
        # Access database URL
        db_url = settings.database.url
        
        # Access MLflow tracking URI
        mlflow_uri = settings.mlflow.tracking_uri
    """
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Service-specific settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    airflow_database: AirflowDatabaseSettings = Field(default_factory=AirflowDatabaseSettings)
    mlflow: MLflowSettings = Field(default_factory=MLflowSettings)
    spark: SparkSettings = Field(default_factory=SparkSettings)
    news_api: NewsAPISettings = Field(default_factory=NewsAPISettings)
    airflow: AirflowSettings = Field(default_factory=AirflowSettings)
    api: APISettings = Field(default_factory=APISettings)


# Global settings instance - import this in your code
settings = Settings()


# Convenience functions for backward compatibility
def get_database_url() -> str:
    """Get database URL (backward compatible)."""
    return settings.database.url


def get_mlflow_tracking_uri() -> str:
    """Get MLflow tracking URI (backward compatible)."""
    return settings.mlflow.tracking_uri

