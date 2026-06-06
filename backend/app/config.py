# ============================================================
#  全局配置 - Pydantic Settings 读取环境变量
# ============================================================
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，从环境变量或 .env 文件读取。"""

    # MySQL
    MYSQL_HOST: str = "mysql"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "pm_user"
    MYSQL_PASSWORD: str = "pm_user_2026"
    MYSQL_DATABASE: str = "project_management"

    # JWT
    JWT_SECRET: str = "pm-jwt-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 2
    REFRESH_EXPIRE_DAYS: int = 7

    # OCR
    OCR_ENGINE: str = "paddleocr"

    # 文件上传
    MAX_FILE_SIZE_MB: int = 20
    UPLOAD_DIR: str = "/app/uploads"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
