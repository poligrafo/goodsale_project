from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SKUBase(BaseModel):
    marketplace_id: int
    product_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    seller_id: Optional[int] = None
    seller_name: Optional[str] = None
    first_image_url: Optional[str] = None
    category_id: int
    category_lvl_1: Optional[str] = None
    category_lvl_2: Optional[str] = None
    category_lvl_3: Optional[str] = None
    category_remaining: Optional[str] = None
    features: Dict[str, Any] = {}
    rating_count: Optional[int] = None
    rating_value: Optional[float] = None
    price_before_discounts: Optional[float] = None
    discount: Optional[float] = None
    price_after_discounts: Optional[float] = None
    bonuses: Optional[int] = None
    sales: Optional[int] = None
    currency: Optional[str] = None
    barcode: Optional[str] = None
    similar_sku: Optional[List[str]] = []


class SKUCreate(SKUBase):
    pass
