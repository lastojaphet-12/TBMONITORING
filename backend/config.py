from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str
    influx_url: str = "http://localhost:8086"
    influx_token: str = "changeme"
    influx_org: str = "tb"
    influx_bucket: str = "monitoring"

    jwt_secret_key: str = "change_me_super_secret"
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60 * 24  # 1 day


settings = Settings()


