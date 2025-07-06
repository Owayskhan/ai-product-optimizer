# engine/optimizer.py
import json
import asyncio
from typing import Dict, List, Any, Optional
import anthropic
import os
from datetime import datetime
import logging

from models.product import ProductInput, OptimizedProduct
from engine.prompts import PRODUCT_OPTIMIZATION_PROMPT, SCHEMA_GENERATION_PROMPT, SHADOW_PAGE_PROMPT

logger = logging.getLogger(__name__)

class ProductOptimizationEngine:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        
        # Updated Anthropic client initialization
        try:
            self.client = anthropic.Anthropic(
                api_key=api_key,
                timeout=30.0,
                max_retries=2
            )
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            # Fallback initialization
            self.client = anthropic.Anthropic(api_key=api_key)
        
        self.model = os.getenv("AI_MODEL", "claude-3-5-sonnet-20241022")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "3000"))
        
        logger.info(f"ProductOptimizationEngine initialized successfully")
        
    async def optimize_product(self, product: ProductInput) -> OptimizedProduct:
        try:
            logger.info(f"Starting optimization for product: {product.product_id}")
            
            # Generate AI optimizations
            optimization_data = await self._generate_optimizations(product)
            
            # Generate schemas
            schema_data = await self._generate_schemas(product, optimization_data)
            
            # Generate shadow page
            shadow_content = await self._generate_shadow_page(product, optimization_data)
            
            # Generate meta data
            meta_data = self._generate_meta_data(product, optimization_data)
            
            # Calculate score
            optimization_score = self._calculate_optimization_score(optimization_data)
            
            optimized_product = OptimizedProduct(
                product_id=product.product_id,
                ai_title=optimization_data.get('ai_title', ''),
                ai_description=optimization_data.get('ai_description', ''),
                semantic_tags=optimization_data.get('semantic_tags', []),
                use_cases=optimization_data.get('use_cases', []),
                json_ld_schema=schema_data,
                shadow_page_content=shadow_content,
                meta_data=meta_data,
                faq_content=optimization_data.get('faq_content', []),
                ai_summary=optimization_data.get('ai_summary', ''),
                conversational_queries=optimization_data.get('conversational_queries', []),
                optimization_score=optimization_score
            )
            
            logger.info(f"Successfully optimized product: {product.product_id}")
            return optimized_product
            
        except Exception as e:
            logger.error(f"Optimization failed for product {product.product_id}: {str(e)}")
            raise Exception(f"Product optimization failed: {str(e)}")
    
    async def optimize_batch(self, products: List[ProductInput], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start_time = datetime.now()
        results = []
        errors = []
        
        max_concurrent = options.get('max_concurrent', 3) if options else 3
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def optimize_with_semaphore(product):
            async with semaphore:
                try:
                    return await self.optimize_product(product)
                except Exception as e:
                    errors.append({
                        "product_id": product.product_id,
                        "error": str(e)
                    })
                    return None
        
        optimization_tasks = [optimize_with_semaphore(product) for product in products]
        optimization_results = await asyncio.gather(*optimization_tasks, return_exceptions=True)
        
        results = [result for result in optimization_results if result is not None and not isinstance(result, Exception)]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        avg_score = sum(r.optimization_score for r in results) / len(results) if results else 0
        
        return {
            "total_products": len(products),
            "successful_optimizations": len(results),
            "failed_optimizations": len(errors),
            "results": results,
            "errors": errors,
            "processing_time": processing_time,
            "average_optimization_score": avg_score
        }
    
    async def _generate_optimizations(self, product: ProductInput) -> Dict[str, Any]:
        prompt = PRODUCT_OPTIMIZATION_PROMPT.format(
            title=product.title,
            description=product.description,
            price=product.price,
            currency=product.currency,
            category=product.category,
            brand=product.brand,
            attributes=json.dumps(product.attributes),
            sku=product.sku or "N/A",
            color=product.color or "N/A",
            size=product.size or "N/A",
            material=product.material or "N/A"
        )
        
        try:
            logger.info("Making request to Anthropic API...")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            logger.info("Received response from Anthropic API")
            
            content = response.content[0].text
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(content)
            logger.info("Successfully parsed optimization data")
            return result
            
        except anthropic.AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            raise Exception(f"Invalid API key: {str(e)}")
        except anthropic.RateLimitError as e:
            logger.error(f"Rate limit error: {str(e)}")
            raise Exception(f"Rate limit exceeded: {str(e)}")
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise Exception(f"Anthropic API error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            raise Exception("Invalid AI response format")
        except Exception as e:
            logger.error(f"Unexpected error in AI optimization: {str(e)}")
            raise Exception(f"AI service error: {str(e)}")
    
    async def _generate_schemas(self, product: ProductInput, optimization_data: Dict) -> Dict[str, Any]:
        try:
            prompt = SCHEMA_GENERATION_PROMPT.format(
                product_data=json.dumps(product.dict(), indent=2),
                optimized_content=json.dumps(optimization_data, indent=2)
            )
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.warning(f"Schema generation failed, using fallback: {e}")
            return self._generate_basic_schema(product, optimization_data)
    
    async def _generate_shadow_page(self, product: ProductInput, optimization_data: Dict) -> str:
        try:
            prompt = SHADOW_PAGE_PROMPT.format(
                product_data=json.dumps(product.dict(), indent=2),
                optimized_data=json.dumps(optimization_data, indent=2)
            )
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.warning(f"Shadow page generation failed, using fallback: {e}")
            return self._generate_basic_shadow_page(product, optimization_data)
    
    def _generate_meta_data(self, product: ProductInput, optimization_data: Dict) -> Dict[str, Any]:
        return {
            "meta_title": optimization_data.get('ai_title', product.title)[:60],
            "meta_description": optimization_data.get('ai_summary', '')[:160],
            "canonical_url": f"/products/{product.product_id}",
            "shadow_url": f"/ai-summary/{product.product_id}",
            "robots": "noindex,follow",
            "last_optimized": datetime.now().isoformat(),
            "optimization_version": "1.0"
        }
    
    def _calculate_optimization_score(self, optimization_data: Dict) -> float:
        score = 0.0
        if optimization_data.get('ai_title'): score += 0.2
        if optimization_data.get('ai_description'): score += 0.2
        if optimization_data.get('semantic_tags'): score += 0.15
        if optimization_data.get('use_cases'): score += 0.15
        if optimization_data.get('faq_content'): score += 0.15
        if optimization_data.get('conversational_queries'): score += 0.15
        return min(score, 1.0)
    
    def _generate_basic_schema(self, product: ProductInput, optimization_data: Dict) -> Dict[str, Any]:
        return {
            "product_schema": {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": optimization_data.get('ai_title', product.title),
                "description": optimization_data.get('ai_description', product.description),
                "brand": {"@type": "Brand", "name": product.brand},
                "offers": {
                    "@type": "Offer",
                    "price": str(product.price),
                    "priceCurrency": product.currency
                }
            },
            "faq_schema": None,
            "review_schema": None
        }
    
    def _generate_basic_shadow_page(self, product: ProductInput, optimization_data: Dict) -> str:
        return f"""
        <div class="ai-optimized-content">
            <h1>{optimization_data.get('ai_title', product.title)}</h1>
            <p>{optimization_data.get('ai_description', product.description)}</p>
            <h2>Perfect For:</h2>
            <ul>
                {''.join([f'<li>{use_case}</li>' for use_case in optimization_data.get('use_cases', [])])}
            </ul>
        </div>
        """
