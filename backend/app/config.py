from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "TV Production Cashflow Generator"
    max_upload_size_mb: int = 50
    temp_dir: str = "/tmp/cashflow"
    allowed_extensions: list[str] = [".xlsx", ".xls"]


settings = Settings()
