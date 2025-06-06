from sqlalchemy import Column, String, DateTime, ForeignKey, UUID, func
from sqlalchemy.orm import relationship
from app.database.base import Base

class CollectionCenter(Base):
    __tablename__ = "collection_centers"

    id = Column(UUID, primary_key=True, index=True)
    # company_id = Column(UUID, ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # company = relationship("Company", back_populates="collection_centers")
    # wholesalers = relationship(
    #     "Wholesaler",
    #     secondary="collection_center_wholesaler",
    #     back_populates="collection_centers"
    # )

class CollectionCenterWholesaler(Base):
    __tablename__ = "collection_center_wholesaler"

    collection_center_id = Column(UUID, ForeignKey("collection_centers.id"), primary_key=True)
    wholesaler_id = Column(UUID, ForeignKey("wholesalers.id"), primary_key=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    # collection_center = relationship("CollectionCenter", back_populates="wholesaler_links")
    # wholesaler = relationship("Wholesaler", back_populates="center_links")