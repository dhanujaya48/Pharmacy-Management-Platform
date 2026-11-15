from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from app.models import MovementType


# ==========================================
# Medicine Schemas
# ==========================================
class MedicineBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, example="Paracetamol 500mg")
    sku: str = Field(..., min_length=2, max_length=50, example="MED-PARA-500")
    dosage_form: str = Field("Tablet", max_length=50, example="Tablet")
    unit_price: float = Field(..., ge=0.0, example=5.50)
    description: Optional[str] = Field(None, max_length=500, example="Analgesic and antipyretic")


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    dosage_form: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[float] = Field(None, ge=0.0)
    description: Optional[str] = Field(None, max_length=500)


class MedicineResponse(MedicineBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Batch Schemas
# ==========================================
class BatchBase(BaseModel):
    batch_number: str = Field(..., min_length=2, max_length=50, example="B001")
    manufacturing_date: date = Field(..., example="2025-01-01")
    expiry_date: date = Field(..., example="2027-12-31")
    initial_quantity: int = Field(..., gt=0, example=100)


class BatchCreate(BatchBase):
    medicine_id: int = Field(..., gt=0, example=1)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.manufacturing_date >= self.expiry_date:
            raise ValueError("manufacturing_date must be strictly earlier than expiry_date")
        return self


class BatchResponse(BaseModel):
    id: int
    medicine_id: int
    batch_number: str
    manufacturing_date: date
    expiry_date: date
    initial_quantity: int
    current_quantity: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Stock Movement Schemas
# ==========================================
class StockTransactionBase(BaseModel):
    batch_id: int = Field(..., gt=0, example=1)
    quantity: int = Field(..., gt=0, description="Quantity must be strictly positive", example=10)
    reference_id: Optional[str] = Field(None, max_length=100, example="INV-2026-001")
    reason: Optional[str] = Field(None, max_length=255, example="Customer Prescription Sale")


class PurchaseRequest(StockTransactionBase):
    reason: Optional[str] = Field("Supplier Restock", max_length=255)


class SaleRequest(StockTransactionBase):
    reason: Optional[str] = Field("Retail Sale", max_length=255)


class ReturnRequest(StockTransactionBase):
    reason: Optional[str] = Field("Customer Return", max_length=255)


class AdjustmentRequest(BaseModel):
    batch_id: int = Field(..., gt=0, example=1)
    adjusted_quantity: int = Field(..., ge=0, description="New target physical count (cannot be negative)", example=45)
    reference_id: Optional[str] = Field(None, max_length=100, example="AUDIT-2026-Q1")
    reason: str = Field(..., min_length=3, max_length=255, example="Stock discrepancy audit correction")


class StockMovementResponse(BaseModel):
    id: int
    batch_id: int
    movement_type: MovementType
    quantity: int
    previous_quantity: int
    new_quantity: int
    reason: Optional[str]
    reference_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Report Schemas
# ==========================================
class BatchStockDetail(BaseModel):
    batch_id: int
    batch_number: str
    expiry_date: date
    current_quantity: int
    is_expired: bool
    status: str


class MedicineInventorySummary(BaseModel):
    medicine_id: int
    medicine_name: str
    sku: str
    unit_price: float
    total_stock: int
    batches: List[BatchStockDetail]


class InventoryReport(BaseModel):
    generated_at: datetime
    total_medicines: int
    total_batches: int
    total_units_in_stock: int
    total_expired_units: int
    medicines: List[MedicineInventorySummary]
