from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from urllib.parse import quote_plus


class Settings(BaseSettings):
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")
    db_host: str | None = None
    db_port: int = 5432
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_sslmode: str = "disable"
    db_pool_min_size: int = 1
    db_pool_max_size: int = 5
    embedding_cache_size: int = 2000

    faucets_category_id: str
    vanities_category_id: str
    lightings_category_id: str
    tiles_category_id: str
    shower_systems_category_id: str
    tubs_category_id: str
    shower_glasses_category_id: str
    mirrors_category_id: str
    toilets_category_id: str
    paints_category_id: str
    lvps_category_id: str
    tub_fillers_category_id: str
    towel_bars_category_id: str
    wallpapers_category_id: str
    toilet_paper_holders_category_id: str
    robe_hooks_category_id: str
    towel_rings_category_id: str
    tub_doors_category_id: str
    shelves_category_id: str
    flooring_category_id: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    def build_database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override

        required = {
            "DB_HOST": self.db_host,
            "DB_NAME": self.db_name,
            "DB_USER": self.db_user,
            "DB_PASSWORD": self.db_password,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(
                "Missing DB settings: "
                + ", ".join(missing)
                + ". Set DB_* variables or DATABASE_URL."
            )

        return (
            "postgresql://"
            f"{quote_plus(self.db_user)}:{quote_plus(self.db_password)}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
            f"?sslmode={self.db_sslmode}"
        )

    @property
    def database_url(self) -> str:
        return self.build_database_url()


settings = Settings()
