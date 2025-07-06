from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class ProductInput(BaseModel):
    product_id: str = Field(..., description="Unique product identifier")
    title: str = Field(..., description="Product title/name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    currency: str = Field(default="USD", description="Currency code")
    category: str = Field(..., description="Primary product category")
    brand: str = Field(..., description="Brand name")
    attributes: Dict[str, Any] = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    existing_reviews: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    availability: str = Field(default="in_stock")
    weight: Optional[float] = Field(None)
    color: Optional[str] = Field(None)
    size: Optional[str] = Field(None)
    material: Optional[str] = Field(None)

class OptimizedProduct(BaseModel):
    product_id: str
    ai_title: str
    ai_description: str
    semantic_tags: List[str]
    use_cases: List[str]
    json_ld_schema: Dict[str, Any]
    shadow_page_content: str
    meta_data: Dict[str, Any]
    faq_content: List[Dict[str, str]]
    optimization_timestamp: datetime = Field(default_factory=datetime.now)
    ai_summary: str
    conversational_queries: List[str]
    optimization_score: float

class BatchOptimizationRequest(BaseModel):
    products: List[ProductInput]
    batch_id: Optional[str] = Field(None)
    optimization_options: Optional[Dict[str, Any]] = Field(default_factory=dict)
