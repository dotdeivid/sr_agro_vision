from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)  # "inference", "copernicus_download", etc.
    status = Column(
        String, nullable=False, default="queued"
    )  # queued, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    config = Column(JSON, nullable=True)  # Task configuration
    result = Column(JSON, nullable=True)  # Task result payload
    error = Column(String, nullable=True)  # Error message on failure

    # Foreign keys
    image_id = Column(String, ForeignKey("images.id"), nullable=True)
    # user_id scopes each task to its owner so listing/status checks can filter by user
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Celery task ID
    celery_task_id = Column(String, nullable=True)

    # Relationships
    image = relationship("Image", backref="tasks")
    user = relationship("User", backref="tasks")
