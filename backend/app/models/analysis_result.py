from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key
    image_id = Column(String, ForeignKey("images.id"), nullable=False)

    # Index type
    index_type = Column(String, nullable=False)  # "ndvi", "evi", "savi", "ndwi"

    # File paths
    result_filepath = Column(String, nullable=False)  # GeoTIFF output
    colormap_filepath = Column(String, nullable=False)  # PNG visualization

    # Statistics (stored as JSON)
    stats = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    image = relationship("Image", backref="analysis_results")
