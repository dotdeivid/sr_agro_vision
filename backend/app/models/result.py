from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Result(Base):
    __tablename__ = "results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign keys
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    original_image_id = Column(String, ForeignKey("images.id"), nullable=False)

    # File paths
    result_filepath = Column(String, nullable=False)

    # Model info
    model_used = Column(String, nullable=False)  # "espcn", "swinir", "gan"
    scale_factor = Column(Integer, nullable=False)  # 2, 4

    # Metrics
    psnr = Column(Float, nullable=True)
    ssim = Column(Float, nullable=True)

    # Additional metadata (renamed from 'metadata' — reserved by SQLAlchemy DeclarativeBase)
    extra_metadata = Column("metadata", JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", backref="results")
    original_image = relationship("Image", backref="sr_results")
