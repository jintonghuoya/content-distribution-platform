import datetime

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PlatformConfig(Base):
    __tablename__ = "platform_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    api_key: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    cookie: Mapped[str] = mapped_column(String(5000), nullable=False, default="")
    app_secret: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    app_id: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
