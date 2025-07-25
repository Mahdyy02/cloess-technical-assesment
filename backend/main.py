from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx
from typing import Optional
from contextlib import asynccontextmanager
from database import db_manager
from chatbot_agent import chatbot_agent
from simple_analytics import SimpleAnalyticsManager
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_manager.create_pool()
    # Initialize simple analytics
    app.state.analytics = SimpleAnalyticsManager(db_manager.pool)
    yield
    # Shutdown
    await db_manager.close_pool()

app = FastAPI(
    title="CLOESS API", 
    description="API for CLOESS Tunisian Fashion Platform",
    lifespan=lifespan
)

origins = [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ProductInteractionRequest(BaseModel):
    product_id: int
    interaction_type: str  # 'hover', 'click', 'view'
    duration_ms: Optional[int] = None
    page_url: Optional[str] = None
    session_id: Optional[str] = None

@app.post('/chat')
async def chat_endpoint(req: ChatRequest):
    if not OPENROUTER_API_KEY:
        return {"response": "[Backend not configured: Please set your OpenRouter API key.]"}
    
    # Generate session ID if not provided
    session_id = req.session_id or f"session_{__import__('uuid').uuid4().hex[:8]}"
    
    try:
        # First, try to handle the request with our agentic chatbot
        agent_response = await chatbot_agent.process_message(req.message, session_id)
        
        if agent_response:
            # Agent handled the request successfully
            return {"response": agent_response, "session_id": session_id}
        
        # If agent couldn't handle it, fall back to AI model with conversation context
        # Get current product context for the AI
        try:
            stats = await db_manager.get_product_stats()
            recent_products = await db_manager.get_products(limit=5)
            
            product_context = f"""
Current CLOESS inventory context:
- Total products: {stats['total_products']}
- Categories: {', '.join([cat['name'] for cat in stats['categories']])}
- Price range: {stats['price_range']['min']:.0f} - {stats['price_range']['max']:.0f} TND

Recent products:
"""
            for product in recent_products:
                product_context += f"- {product['name']}: {product['price']} TND ({product['category']})\n"
                
        except Exception as e:
            product_context = "I can help you with questions about our Tunisian fashion products."
        
        # Get conversation context from agent
        conversation_context = chatbot_agent._get_conversation_context(session_id)
        conversation_history = chatbot_agent._get_conversation_history(session_id)
        
        # Check if this is the first interaction in the session
        is_first_message = len([msg for msg in conversation_history if msg["role"] == "user"]) <= 1
        
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
        }
        
        greeting_instruction = ""
        if is_first_message:
            greeting_instruction = """- This is the first message in the conversation, so start with a warm Arabic greeting like "Asleema" or "Ahlan wa sahlan"
- After the greeting, introduce yourself as Amira from CLOESS"""
        else:
            greeting_instruction = """- This is a continuing conversation, so DO NOT repeat greetings like "Welcome to CLOESS" or "Asleema" 
- Continue the conversation naturally without introductions"""
        
        system_prompt = f"""You are Amira, a friendly Tunisian clothing seller at CLOESS. You specialize in traditional Tunisian artisanat and fashion.

{product_context}

{conversation_context}

Guidelines:
{greeting_instruction}
- Be warm and helpful in your responses
- Focus on Tunisian cultural heritage and craftsmanship
- If asked about specific products, mention that you can search our current inventory
- Keep responses concise but informative
- Use emojis occasionally to be friendly
- If users ask about products not in context, suggest they ask for a product search
- Remember the conversation context and provide relevant follow-up responses
- Use markdown formatting for emphasis (**bold text**)
- NEVER repeat welcome messages or greetings in ongoing conversations

Answer questions about CLOESS, Tunisian artisanat, shopping, and fashion. Be helpful and welcoming."""

        payload = {
            "model": "mistralai/mistral-small-3.1-24b-instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message}
            ],
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient() as client:
            r = await client.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                ai_response = data['choices'][0]['message']['content']
                
                # Add AI response to conversation history
                chatbot_agent._add_to_conversation(session_id, "bot", ai_response)
                
                return {"response": ai_response, "session_id": session_id}
            else:
                error_response = "Sorry, I could not get a response from the AI provider."
                chatbot_agent._add_to_conversation(session_id, "bot", error_response)
                return {"response": error_response, "session_id": session_id}
                
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        error_response = "I'm having some technical difficulties. Please try again in a moment!"
        chatbot_agent._add_to_conversation(session_id, "bot", error_response)
        return {"response": error_response, "session_id": session_id}

# Product endpoints
@app.get("/products/search")
async def search_products(
    q: str = Query(..., description="Search term for products"),
    limit: int = Query(20, ge=1, le=50, description="Number of results to return")
):
    """Search products by name, description, or category"""
    try:
        products = await db_manager.search_products(q, limit)
        return {
            "products": products,
            "count": len(products),
            "search_term": q,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search products: {str(e)}")

@app.get("/products/price-range")
async def get_products_by_price_range(
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    limit: int = Query(20, ge=1, le=50, description="Number of results to return")
):
    """Get products within a specific price range"""
    try:
        products = await db_manager.get_products_by_price_range(min_price, max_price, limit)
        return {
            "products": products,
            "count": len(products),
            "price_range": {
                "min": min_price,
                "max": max_price
            },
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch products by price: {str(e)}")

@app.get("/products/stats")
async def get_product_statistics():
    """Get comprehensive product statistics"""
    try:
        stats = await db_manager.get_product_stats()
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch product statistics: {str(e)}")

@app.get("/products")
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip")
):
    """Get all products or filter by category"""
    try:
        products = await db_manager.get_products(category=category, limit=limit, offset=offset)
        return {
            "products": products,
            "count": len(products),
            "category": category,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """Get a specific product by ID"""
    try:
        product = await db_manager.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"product": product}
    except Exception as e:
        if "Product not found" in str(e):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to fetch product: {str(e)}")

@app.get("/categories")
async def get_categories():
    """Get all available product categories"""
    try:
        categories = await db_manager.get_categories()
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")

@app.get("/products/search")
async def search_products(
    q: str = Query(..., description="Search term for products"),
    limit: int = Query(20, ge=1, le=50, description="Number of results to return")
):
    """Search products by name, description, or category"""
    try:
        products = await db_manager.search_products(q, limit)
        return {
            "products": products,
            "count": len(products),
            "search_term": q,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search products: {str(e)}")

@app.get("/products/price-range")
async def get_products_by_price_range(
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    limit: int = Query(20, ge=1, le=50, description="Number of results to return")
):
    """Get products within a specific price range"""
    try:
        products = await db_manager.get_products_by_price_range(min_price, max_price, limit)
        return {
            "products": products,
            "count": len(products),
            "price_range": {
                "min": min_price,
                "max": max_price
            },
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch products by price: {str(e)}")

@app.get("/products/stats")
async def get_product_statistics():
    """Get comprehensive product statistics"""
    try:
        stats = await db_manager.get_product_stats()
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch product statistics: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "CLOESS API is running"}

# Analytics endpoints
@app.post("/analytics/track-interaction")
async def track_product_interaction(req: ProductInteractionRequest, request: Request):
    """Track user product interactions (hover, click, view) - invisible tracking"""
    try:
        # Get client IP address
        client_ip = request.client.host
        if hasattr(request, 'headers') and 'x-forwarded-for' in request.headers:
            client_ip = request.headers['x-forwarded-for'].split(',')[0].strip()
        elif hasattr(request, 'headers') and 'x-real-ip' in request.headers:
            client_ip = request.headers['x-real-ip']
        
        # Get user agent
        user_agent = request.headers.get('user-agent', '')
        
        # Track or get user session
        user_session_id = await app.state.analytics.track_user_session(client_ip, user_agent)
        
        # Track the product interaction
        await app.state.analytics.track_product_interaction(
            user_session_id=user_session_id,
            product_id=req.product_id,
            interaction_type=req.interaction_type,
            duration_ms=req.duration_ms,
            page_url=req.page_url,
            session_id=req.session_id
        )
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"Analytics tracking error: {e}")
        # Don't fail the request for analytics errors
        return {"status": "error"}

@app.post("/analytics/session")
async def track_user_session(request: Request):
    """Track user session (called when user visits the site)"""
    try:
        # Get client IP address
        client_ip = request.client.host
        if hasattr(request, 'headers') and 'x-forwarded-for' in request.headers:
            client_ip = request.headers['x-forwarded-for'].split(',')[0].strip()
        elif hasattr(request, 'headers') and 'x-real-ip' in request.headers:
            client_ip = request.headers['x-real-ip']
        
        # Get user agent
        user_agent = request.headers.get('user-agent', '')
        
        # Track user session
        user_session_id = await app.state.analytics.track_user_session(client_ip, user_agent)
        
        return {"status": "success", "user_session_id": user_session_id}
        
    except Exception as e:
        print(f"Session tracking error: {e}")
        return {"status": "error"}

@app.get("/analytics/users")
async def get_user_analytics(limit: int = Query(100, ge=1, le=1000)):
    """Get user analytics data"""
    try:
        analytics = await app.state.analytics.get_user_analytics(limit)
        return {"users": analytics, "count": len(analytics)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user analytics: {str(e)}")

@app.get("/analytics/products")
async def get_product_analytics(product_id: Optional[int] = Query(None)):
    """Get product interaction analytics"""
    try:
        analytics = await app.state.analytics.get_product_analytics(product_id)
        return {"products": analytics, "count": len(analytics)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch product analytics: {str(e)}")

@app.get("/analytics/countries")
async def get_country_analytics():
    """Get analytics by country"""
    try:
        analytics = await app.state.analytics.get_country_analytics()
        return {"countries": analytics, "count": len(analytics)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch country analytics: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 