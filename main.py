from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime
import os
import json
import csv
import io
from dotenv import load_dotenv
import anthropic

load_dotenv()

from models.product import ProductInput, OptimizedProduct, BatchOptimizationRequest
from engine.optimizer import ProductOptimizationEngine
from exporters.feed_generators import FeedExporter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Product Optimization Engine", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize services
exporter = FeedExporter()
batch_results = {}

# API Key extraction
def get_api_key():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return api_key

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/test-key")
async def test_api_key():
    try:
        api_key = get_api_key()
        
        if not api_key:
            return {
                "status": "error",
                "message": "API key not found in environment variables"
            }
        
        if not api_key.startswith("sk-ant-"):
            return {
                "status": "error",
                "message": "Invalid API key format. Should start with 'sk-ant-'"
            }
        
        # Test with a simple client initialization
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test message
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Hello, respond with 'API working'"}]
        )
        
        return {
            "status": "success",
            "message": "API key is working correctly",
            "response": response.content[0].text,
            "api_key_prefix": api_key[:15] + "..."
        }
        
    except anthropic.AuthenticationError as e:
        return {
            "status": "error",
            "message": f"Authentication failed: {str(e)}"
        }
    except anthropic.APIError as e:
        return {
            "status": "error",
            "message": f"API error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

@app.post("/api/optimize-product")
async def optimize_product(product: ProductInput):
    try:
        api_key = get_api_key()
        optimizer = ProductOptimizationEngine(api_key=api_key)
        result = await optimizer.optimize_product(product)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize-batch")
async def optimize_batch(request: BatchOptimizationRequest):
    try:
        api_key = get_api_key()
        optimizer = ProductOptimizationEngine(api_key=api_key)
        
        batch_id = request.batch_id or str(uuid.uuid4())
        result = await optimizer.optimize_batch(request.products, request.optimization_options)
        result['batch_id'] = batch_id
        
        batch_results[batch_id] = result
        
        return {
            "batch_id": batch_id,
            "status": "completed",
            "summary": {
                "total_products": result['total_products'],
                "successful": result['successful_optimizations'],
                "failed": result['failed_optimizations'],
                "processing_time": result['processing_time'],
                "average_score": result.get('average_optimization_score', 0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/batch-result/{batch_id}")
async def get_batch_result(batch_id: str):
    if batch_id not in batch_results:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch_results[batch_id]

@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(decoded))
        products = []
        
        for row in csv_reader:
            # Basic mapping
            product_data = {
                "product_id": row.get("id", row.get("product_id", f"prod-{len(products)+1}")),
                "title": row.get("title", row.get("name", "")),
                "description": row.get("description", ""),
                "price": float(row.get("price", 0) or 0),
                "category": row.get("category", ""),
                "brand": row.get("brand", ""),
                "currency": row.get("currency", "USD"),
                "sku": row.get("sku", ""),
                "color": row.get("color", ""),
                "size": row.get("size", ""),
                "material": row.get("material", "")
            }
            
            # Validate required fields
            if all([product_data["product_id"], product_data["title"], product_data["description"], 
                   product_data["price"] > 0, product_data["category"], product_data["brand"]]):
                products.append(ProductInput(**product_data))
        
        return {
            "message": f"Successfully parsed {len(products)} products",
            "products": products
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing failed: {str(e)}")

@app.get("/api/export/google-merchant/{batch_id}")
async def export_google_merchant(batch_id: str):
    if batch_id not in batch_results:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    try:
        products = batch_results[batch_id]['results']
        xml_content = exporter.generate_google_merchant_xml(products)
        
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename=google_merchant_{batch_id}.xml"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/meta-csv/{batch_id}")
async def export_meta_csv(batch_id: str):
    if batch_id not in batch_results:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    try:
        products = batch_results[batch_id]['results']
        csv_content = exporter.generate_meta_tiktok_csv(products)
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=meta_feed_{batch_id}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
