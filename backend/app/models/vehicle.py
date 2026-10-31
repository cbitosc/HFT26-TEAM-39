from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(String(64), nullable=False)  # Telemetry / identifier ID (e.g. VEH_1, VIN)
    make_model = Column(String(128), nullable=True)
    color = Column(String(64), nullable=True)
    license_plate = Column(String(32), nullable=True)
    role = Column(String(64), nullable=True)  # e.g., "PRIMARY_VEHICLE", "COLLIDING_VEHICLE", "WITNESS"

    # Relationships
    incident = relationship("Incident", back_populates="vehicles")
