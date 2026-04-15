import datetime
import enum

from sqlalchemy import JSON, DateTime, Enum, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TopicStatus(str, enum.Enum):
    PENDING = "pending"
    FILTERED = "filtered"
    REJECTED = "rejected"
    GENERATING = "generating"
    PUBLISHED = "published"


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heat_value: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    collected_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[TopicStatus] = mapped_column(
        Enum(TopicStatus, values_callable=lambda x: [e.value for e in x]),
        default=TopicStatus.PENDING,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
