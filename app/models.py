from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    Enum as SQLEnum,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base


class MovementType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    RETURN = "RETURN"
    ADJUSTMENT = "ADJUSTMENT"


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    dosage_form = Column(String(50), nullable=False, default="Tablet")  # e.g., Tablet, Syrup, Injection
    unit_price = Column(Float, nullable=False, default=0.0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    batches = relationship("Batch", back_populates="medicine", cascade="all, delete-orphan")


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_number = Column(String(50), nullable=False, index=True)
    manufacturing_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    initial_quantity = Column(Integer, nullable=False, default=0)
    current_quantity = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("current_quantity >= 0", name="check_positive_batch_quantity"),
        Index("idx_batch_med_expiry", "medicine_id", "expiry_date"),
    )

    medicine = relationship("Medicine", back_populates="batches")
    movements = relationship("StockMovement", back_populates="batch", cascade="all, delete-orphan")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_type = Column(SQLEnum(MovementType), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    previous_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    reference_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    batch = relationship("Batch", back_populates="movements")
