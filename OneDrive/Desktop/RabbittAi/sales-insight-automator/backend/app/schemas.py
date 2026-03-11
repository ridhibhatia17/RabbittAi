from pydantic import BaseModel, EmailStr


class AnalyzeSalesResponse(BaseModel):
    status: str
    message: str


class EmailRequest(BaseModel):
    recipient_email: EmailStr


class SalesMetrics(BaseModel):
    total_revenue: float
    top_category: str
    top_region: str
    total_units: int
    cancelled_orders: int
    completed_orders: int
    cancelled_ratio: float
