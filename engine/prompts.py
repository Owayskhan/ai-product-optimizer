PRODUCT_OPTIMIZATION_PROMPT = """
You are an expert e-commerce AI optimization specialist. Optimize this product data for AI shopping assistants like ChatGPT, Google Gemini, Perplexity, and DeepSeek.

PRODUCT DATA:
Title: {title}
Description: {description}
Price: ${price} {currency}
Category: {category}
Brand: {brand}
Attributes: {attributes}
SKU: {sku}
Color: {color}
Size: {size}
Material: {material}

Create content that performs exceptionally well when AI assistants search for and recommend products.

1. AI-OPTIMIZED TITLE (55-60 characters):
- Lead with primary benefit/value proposition
- Include natural language keywords for voice search
- Make it conversational and specific

2. BENEFIT-LED DESCRIPTION (180-220 words):
- Start with the #1 benefit that solves a problem
- Use conversational, natural language
- Include use cases and scenarios
- Address common questions AI assistants ask

3. SEMANTIC TAGS (12-15 tags):
- Natural language phrases, not just keywords
- Include question-based tags ("What's the best...", "How to...")
- Problem-solving tags ("reduces stress", "saves time")

4. USE CASES (6-8 specific scenarios):
- Detailed situations where this product excels
- Include user personas and contexts
- Price-point positioning if relevant

5. FAQ CONTENT (6-8 Q&A pairs):
- Questions AI assistants commonly ask
- Questions real users ask about this product category
- Address concerns and objections

6. AI SUMMARY (80-100 words):
- Concise overview optimized for AI understanding
- Include key differentiators

7. CONVERSATIONAL QUERIES (8-10 natural language queries):
- How users might ask AI assistants about this product
- Include voice search patterns

Return your response in this exact JSON format:
{{
  "ai_title": "optimized title here",
  "ai_description": "benefit-led description here",
  "semantic_tags": ["tag1", "tag2", "tag3"],
  "use_cases": ["use case 1", "use case 2"],
  "faq_content": [
    {{"question": "question 1", "answer": "answer 1"}},
    {{"question": "question 2", "answer": "answer 2"}}
  ],
  "ai_summary": "concise summary here",
  "conversational_queries": ["query1", "query2"]
}}
"""

SCHEMA_GENERATION_PROMPT = """
Generate JSON-LD schema markup for this product optimized for AI assistants.

PRODUCT: {product_data}
OPTIMIZED CONTENT: {optimized_content}

Create Product, FAQ, and Review schemas that help AI understand and recommend this product.

Return as valid JSON-LD in this format:
{{
  "product_schema": {{"@context": "https://schema.org/", "@type": "Product", "name": "...", "description": "..."}},
  "faq_schema": {{"@context": "https://schema.org/", "@type": "FAQPage", "mainEntity": [...]}},
  "review_schema": null
}}
"""

SHADOW_PAGE_PROMPT = """
Create AI-optimized HTML content for this product's shadow page.

PRODUCT: {product_data}
OPTIMIZED DATA: {optimized_data}

Create comprehensive HTML content with:
- Benefit-focused headlines
- Natural language explanations
- FAQ sections
- Comparison information

Return clean HTML content ready for deployment.
"""
