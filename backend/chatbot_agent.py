from typing import Dict, List, Any
from database import db_manager
import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class ChatbotAgent:
    """Agentic chatbot using LLM-based intent detection for natural conversation"""
    
    def __init__(self):
        self.tools = {
            "search_products": self._search_products,
            "get_products_by_category": self._get_products_by_category,
            "get_products_by_price": self._get_products_by_price,
            "get_product_stats": self._get_product_stats,
            "get_all_categories": self._get_all_categories,
            "get_product_stock": self._get_product_stock
        }
        # Conversation memory storage - session_id -> conversation history
        self.conversations = {}
        # Track if we've already greeted users in each session
        self.session_greeted = {}
    
    async def _detect_intent_with_llm(self, message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Use actual LLM to detect intent. This provides true natural language understanding
        rather than hardcoded pattern matching.
        """
        # Build conversation context for the LLM
        context = self._build_conversation_context(conversation_history)
        
        # Create the intent detection prompt with dynamic categories
        prompt = await self._create_intent_detection_prompt(message, context)
        
        try:
            # Here we would call an actual LLM (OpenAI, Anthropic, etc.)
            # For now, we'll use a fallback to the enhanced pattern matching
            # TODO: Replace with actual LLM API call
            intent_result = await self._call_llm_for_intent(prompt)
            
            # Validate the LLM response format
            if self._validate_intent_response(intent_result):
                return intent_result
            else:
                # Fallback to enhanced pattern matching if LLM response is invalid
                return self._fallback_intent_detection(message, conversation_history)
                
        except Exception as e:
            print(f"LLM intent detection failed: {e}, falling back to pattern matching")
            return self._fallback_intent_detection(message, conversation_history)
    
    def _build_conversation_context(self, conversation_history: List[Dict] = None) -> str:
        """Build conversation context for intent detection"""
        if not conversation_history:
            return "No previous conversation."
        
        # Extract recently mentioned products and topics
        context_info = {
            "recent_products": [],
            "recent_topics": [],
            "last_intent": None
        }
        
        # Analyze last 3 messages for context
        for msg in conversation_history[-3:]:
            msg_text = msg["message"].lower()
            
            # Extract product mentions
            product_keywords = {
                "carthagean robe": ["carthagean", "robe"],
                "kaftan": ["kaftan"],
                "fouta towel": ["fouta", "towel"],
                "carpet": ["carpet", "rug", "berber"],
                "bag": ["bag"],
                "jewelry": ["jewelry", "jewellery", "silver"],
                "bowl": ["bowl", "olive wood"],
                "shawl": ["shawl", "artisan"]
            }
            
            for product_name, keywords in product_keywords.items():
                if any(keyword in msg_text for keyword in keywords):
                    if product_name not in context_info["recent_products"]:
                        context_info["recent_products"].append(product_name)
        
        # Format context string
        context = ""
        if context_info["recent_products"]:
            context += f"Recently discussed products: {', '.join(context_info['recent_products'])}. "
        
        # Add last user message for immediate context
        if conversation_history:
            last_user_msg = None
            for msg in reversed(conversation_history):
                if msg["role"] == "user":
                    last_user_msg = msg["message"]
                    break
            if last_user_msg:
                context += f"Previous user message: '{last_user_msg}'"
        
        return context or "No relevant context."
    
    async def _create_intent_detection_prompt(self, message: str, context: str) -> str:
        """Create the prompt for LLM intent detection with dynamic product categories"""
        try:
            # Get categories dynamically from database
            categories = await db_manager.get_categories()
            category_list = "\n".join([f"- {category}" for category in categories])
        except Exception as e:
            print(f"Error fetching categories for prompt: {e}")
            # Fallback to basic categories if database fails
            category_list = "- Traditional Wear\n- Home Decor\n- Accessories\n- Artisan Crafts"
        
        prompt = f"""You are an intent detection module for a Tunisian artisanat e-commerce chatbot. 
Given a user message and conversation context, determine the intent and extract relevant parameters.

AVAILABLE INTENTS:
1. "get_product_info_for_llm" - User wants product information (search, stock check, or details)
   - info_type: "search" (looking for products), "stock" (checking availability), "details" (asking about specific product features)
   - product_search: specific product name or general category

2. "general_conversation" - General chat, greetings, or questions not requiring database access
   - message: the original user message

PRODUCT CATEGORIES WE SELL:
{category_list}

CONTEXT: {context}
USER MESSAGE: "{message}"

Respond with ONLY a JSON object in this exact format:
{{
  "intent": "intent_name",
  "params": {{
    "key": "value"
  }},
  "confidence": 0.0-1.0
}}

Examples:
- "Do you have robes in stock?" → {{"intent": "get_product_info_for_llm", "params": {{"product_search": "robe", "info_type": "stock"}}, "confidence": 0.9}}
- "Is this good for weddings?" (when carthagean robe was discussed) → {{"intent": "get_product_info_for_llm", "params": {{"product_search": "carthagean robe", "info_type": "details"}}, "confidence": 0.95}}
- "Hello, how are you?" → {{"intent": "general_conversation", "params": {{"message": "Hello, how are you?"}}, "confidence": 0.9}}"""

        return prompt
    
    async def _call_llm_for_intent(self, prompt: str) -> Dict[str, Any]:
        """
        Call actual LLM for intent detection using OpenRouter API
        """
        
        if not OPENROUTER_API_KEY:
            # Fallback to simulation if no API key
            return self._simulate_llm_intent_response(prompt)
        
        try:
            headers = {
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
            }
            
            payload = {
                "model": "mistralai/mistral-small-3.1-24b-instruct",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 150,  # Keep it short for intent detection
                "temperature": 0.1  # Low temperature for consistent intent detection
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    llm_response = data['choices'][0]['message']['content'].strip()
                    
                    # Try to parse the JSON response
                    try:
                        intent_result = json.loads(llm_response)
                        return intent_result
                    except json.JSONDecodeError:
                        # If LLM didn't return valid JSON, fall back to simulation
                        print(f"LLM returned invalid JSON: {llm_response}")
                        return self._simulate_llm_intent_response(prompt)
                else:
                    print(f"OpenRouter API error: {response.status_code}")
                    return self._simulate_llm_intent_response(prompt)
                    
        except Exception as e:
            print(f"Error calling OpenRouter API for intent: {e}")
            return self._simulate_llm_intent_response(prompt)
        
    
    def _simulate_llm_intent_response(self, prompt: str) -> Dict[str, Any]:
        """
        Simplified fallback for intent detection when LLM API fails.
        Only used as emergency backup - the real LLM handles most cases.
        """
        # Extract the user message from the prompt
        message_start = prompt.find('USER MESSAGE: "') + len('USER MESSAGE: "')
        message_end = prompt.find('"', message_start)
        message = prompt[message_start:message_end].lower()
        
        # Simple fallback patterns
        if any(word in message for word in ["stock", "available", "how many", "do you have"]):
            return {
                "intent": "get_product_info_for_llm",
                "params": {"product_search": "", "info_type": "stock"},
                "confidence": 0.7
            }
        elif any(word in message for word in ["good for", "suitable for", "perfect for", "about this"]):
            return {
                "intent": "get_product_info_for_llm",
                "params": {"product_search": "", "info_type": "details"},
                "confidence": 0.7
            }
        elif any(word in message for word in ["looking for", "need", "want", "show me", "find", "search"]):
            return {
                "intent": "get_product_info_for_llm",
                "params": {"product_search": "products", "info_type": "search"},
                "confidence": 0.7
            }
        else:
            return {
                "intent": "general_conversation",
                "params": {"message": message},
                "confidence": 0.8
            }
    
    def _validate_intent_response(self, response: Dict[str, Any]) -> bool:
        """Validate that the LLM response has the correct format"""
        if not isinstance(response, dict):
            return False
        
        required_keys = ["intent", "params", "confidence"]
        if not all(key in response for key in required_keys):
            return False
        
        valid_intents = ["get_product_info_for_llm", "general_conversation"]
        if response["intent"] not in valid_intents:
            return False
        
        if not isinstance(response["confidence"], (int, float)) or not (0 <= response["confidence"] <= 1):
            return False
        
        return True
    
    def _fallback_intent_detection(self, message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Enhanced fallback pattern matching if LLM fails"""
        message_lower = message.lower()
        
        # Simple pattern-based fallback
        if any(word in message_lower for word in ["stock", "available", "how many"]):
            return {
                "intent": "get_product_info_for_llm",
                "params": {"product_search": "", "info_type": "stock"},
                "confidence": 0.7
            }
        elif any(word in message_lower for word in ["looking for", "need", "want", "show"]):
            return {
                "intent": "get_product_info_for_llm",
                "params": {"product_search": "products", "info_type": "search"},
                "confidence": 0.7
            }
        else:
            return {
                "intent": "general_conversation",
                "params": {"message": message},
                "confidence": 0.8
            }
    
    def _extract_product_name_intelligently(self, message: str) -> str:
        """Extract product name using natural language understanding"""
        product_keywords = {
            "robe": ["robe", "robes", "carthagean"],
            "kaftan": ["kaftan", "kaftans"],
            "fouta towel": ["towel", "towels", "fouta"],
            "carpet": ["carpet", "carpets", "rug", "rugs", "berber"],
            "bag": ["bag", "bags"],
            "jewelry": ["jewelry", "jewellery", "silver"],
            "bowl": ["bowl", "bowls", "olive", "wood"],
            "shawl": ["shawl", "shawls", "artisan"]
        }
        
        for product_type, keywords in product_keywords.items():
            if any(keyword in message for keyword in keywords):
                return product_type
        return ""
    
    async def process_message(self, message: str, session_id: str = "default") -> str:
        """Process user message using LLM-based intent detection"""
        try:
            # Add user message to conversation history
            self._add_to_conversation(session_id, "user", message)
            
            # Get conversation history for context
            history = self._get_conversation_history(session_id)
            
            # Use LLM-based intent detection
            intent_result = await self._detect_intent_with_llm(message, history)
            intent_type = intent_result["intent"]
            params = intent_result["params"]
            confidence = intent_result["confidence"]
            
            print(f"Debug - Intent: {intent_type}, Params: {params}, Confidence: {confidence}")
            
            if intent_type == "get_product_info_for_llm":
                # Get product information and let the main LLM handle the response
                product_search = params.get("product_search", "")
                info_type = params.get("info_type", "search")
                
                if info_type == "search":
                    if product_search:
                        products = await self._search_products(product_search)
                    else:
                        products = await db_manager.get_products(limit=6)
                    
                    # Prepare context for LLM instead of formatting response ourselves
                    product_context = self._prepare_product_context_for_llm(products, product_search)
                    
                elif info_type == "stock":
                    if product_search:
                        products = await self._get_product_stock(product_search)
                        product_context = self._prepare_stock_context_for_llm(products, product_search)
                    else:
                        product_context = "No specific product mentioned for stock check."
                        
                elif info_type == "details":
                    if product_search:
                        products = await self._search_products(product_search)
                        product_context = self._prepare_detailed_context_for_llm(products, product_search)
                    else:
                        product_context = "No specific product mentioned for details."
                
                # Add the product context to conversation and return None to let main LLM handle
                self._add_product_context_to_conversation(session_id, product_context)
            
            elif intent_type == "stock_check":
                product_name = params.get("product_name", "")
                if product_name:
                    products = await self._get_product_stock(product_name)
                    product_context = self._prepare_stock_context_for_llm(products, product_name)
                    self._add_product_context_to_conversation(session_id, product_context)
            
            return None
                
        except Exception as e:
            print(f"Error in chatbot agent: {e}")
            error_response = "I'm having trouble accessing our product database right now. Please try again in a moment!"
            self._add_to_conversation(session_id, "bot", error_response)
            return error_response
    
    def _format_stats_response(self, stats: Dict[str, Any], session_id: str = None) -> str:
        """Format statistics into a natural response without repetitive greetings"""
        greeting = ""
        if session_id and not self._has_been_greeted(session_id):
            greeting = "Welcome to CLOESS! "
            self.session_greeted[session_id] = True
        
        response = f"{greeting}Here's what we offer:\n\n"
        response += f"📦 **{stats['total_products']} unique products** across {stats['total_categories']} categories\n"
        response += f"💰 **Price range**: {stats['price_range']['min']:.0f} - {stats['price_range']['max']:.0f} TND\n"
        response += f"📊 **Average price**: {stats['price_range']['average']:.0f} TND\n\n"
        
        response += "**Our categories:**\n"
        for category in stats['categories']:
            response += f"• {category['name']} ({category['count']} items, avg {category['avg_price']:.0f} TND)\n"
        
        response += "\nWhat specific type of Tunisian artisanat interests you today?"
        return response
    

    def _has_been_greeted(self, session_id: str) -> bool:
        """Check if this session has already been greeted"""
        return session_id in self.session_greeted
    
    def _get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        return self.conversations.get(session_id, [])
    
    def _get_conversation_context(self, session_id: str) -> str:
        """Get conversation context as a formatted string for AI model"""
        history = self._get_conversation_history(session_id)
        if not history:
            return "No previous conversation."
        
        context = "Previous conversation:\n"
        for msg in history[-5:]:  # Last 5 messages for context
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['message']}\n"
        
        return context
    
    def _add_to_conversation(self, session_id: str, role: str, message: str):
        """Add a message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            "role": role,
            "message": message,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
        # Keep only last 10 messages to prevent memory bloat
        if len(self.conversations[session_id]) > 10:
            self.conversations[session_id] = self.conversations[session_id][-10:]
    
    async def _search_products(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for products with improved matching"""
        # First try the original search
        products = await db_manager.search_products(search_term)
        
        # If no results, try intelligent alternative searches
        if not products and search_term:
            query_lower = search_term.lower()
            alternative_searches = []
            
            # Smart mapping for common search terms
            if "robe" in query_lower or "robes" in query_lower:
                alternative_searches = ["carthagean", "kaftan", "traditional"]
            elif "towel" in query_lower or "fouta" in query_lower:
                alternative_searches = ["fouta", "towel", "traditional"]
            elif "carpet" in query_lower or "rug" in query_lower:
                alternative_searches = ["carpet", "berber", "traditional"]
            elif "bag" in query_lower:
                alternative_searches = ["bag", "handmade", "leather"]
            elif "jewelry" in query_lower or "jewellery" in query_lower:
                alternative_searches = ["jewelry", "silver", "artisan"]
            elif "formal" in query_lower or "wedding" in query_lower:
                alternative_searches = ["carthagean", "kaftan", "robe", "traditional"]
            
            # Try alternative searches
            for alt_search in alternative_searches:
                alt_products = await db_manager.search_products(alt_search)
                if alt_products:
                    products.extend(alt_products)
                    break  # Stop after first successful alternative
        
        return products
    
    async def _get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products from a specific category"""
        return await db_manager.get_products(category=category, limit=20)
    
    async def _get_products_by_price(self, min_price: float = None, max_price: float = None) -> List[Dict[str, Any]]:
        """Get products within a price range"""
        return await db_manager.get_products_by_price_range(min_price, max_price)
    
    async def _get_product_stats(self) -> Dict[str, Any]:
        """Get overall product statistics"""
        return await db_manager.get_product_stats()
    
    async def _get_all_categories(self) -> List[str]:
        """Get all available categories"""
        return await db_manager.get_categories()
    
    async def _get_product_stock(self, product_name: str) -> List[Dict[str, Any]]:
        """Get stock information for a specific product with improved matching"""
        # First try the original search
        products = await db_manager.search_products(product_name)
        
        # If no results and it's a common term, try intelligent alternatives
        if not products and product_name:
            query_lower = product_name.lower()
            alternative_searches = []
            
            if query_lower in ["robe", "robes"]:
                alternative_searches = ["carthagean", "kaftan", "traditional"]
            elif query_lower in ["towel", "towels"]:
                alternative_searches = ["fouta", "towel", "traditional"]
            elif query_lower in ["carpet", "carpets", "rug", "rugs"]:
                alternative_searches = ["carpet", "berber", "traditional"]
            elif query_lower in ["bag", "bags"]:
                alternative_searches = ["bag", "handmade", "leather"]
            elif query_lower in ["jewelry", "jewellery"]:
                alternative_searches = ["jewelry", "silver", "artisan"]
            elif query_lower in ["bowl", "bowls"]:
                alternative_searches = ["bowl", "olive", "wood"]
            elif query_lower in ["shawl", "shawls"]:
                alternative_searches = ["shawl", "artisan", "traditional"]
            
            # Try alternative searches
            for alt_search in alternative_searches:
                alt_products = await db_manager.search_products(alt_search)
                if alt_products:
                    products.extend(alt_products)
            
            # Remove duplicates based on product ID
            if products:
                seen_ids = set()
                unique_products = []
                for product in products:
                    if product['id'] not in seen_ids:
                        seen_ids.add(product['id'])
                        unique_products.append(product)
                products = unique_products
        
        return products
    
    def _format_products_response(self, products: List[Dict[str, Any]], context: str = "", session_id: str = None) -> str:
        """Format products into a natural response without repetitive greetings"""
        if not products:
            return "I'm sorry, I couldn't find any products matching your request. Would you like me to show you our full collection instead?"
        
        if len(products) == 1:
            product = products[0]
            return f"I found exactly what you're looking for! We have the **{product['name']}** for {product['price']} {product['currency']}. {product['description']} We currently have {product['stock_quantity']} in stock."
        
        # Only add greeting if this is the very first interaction in the session
        greeting = ""
        if session_id and not self._has_been_greeted(session_id):
            greeting = "Welcome to CLOESS! "
            self.session_greeted[session_id] = True
        
        if len(products) <= 3:
            response = f"{greeting}Here are the {len(products)} products I found for you:\n\n"
            for product in products:
                response += f"• **{product['name']}** - {product['price']} {product['currency']}\n"
                response += f"  {product['description'][:100]}{'...' if len(product['description']) > 100 else ''}\n\n"
        else:
            response = f"{greeting}I found {len(products)} wonderful products for you! Here are the top 3:\n\n"
            for product in products[:3]:
                response += f"• **{product['name']}** - {product['price']} {product['currency']}\n"
            response += f"\nWould you like me to show you more options or help you narrow down your search?"
        
        return response
    
    def _format_stock_response(self, products: List[Dict[str, Any]], query_product: str) -> str:
        """Format stock information into a natural response"""
        if not products:
            # Try alternative searches for common product types if nothing found
            suggestion_text = f"I'm sorry, but we don't currently have any '{query_product}' in stock."
            
            # Suggest related searches - handle plurals and variations
            query_lower = query_product.lower()
            if "fouta" in query_lower or "towel" in query_lower:
                suggestion_text += " Did you mean to ask about our **fouta towels**? They're one of our most popular traditional Tunisian items!"
            elif "robe" in query_lower:
                suggestion_text += " Did you mean to ask about our **Carthagean Robe** or **Tunisian Kaftan**? Both are beautiful traditional robes!"
            elif "carpet" in query_lower or "rug" in query_lower:
                suggestion_text += " Did you mean to ask about our **traditional carpets**?"
            elif "bag" in query_lower:
                suggestion_text += " Did you mean to ask about our **traditional bags**?"
            else:
                suggestion_text += " Would you like me to suggest some similar items or show you our available products?"
            
            return suggestion_text
        
        # Find exact or closest match with improved plural/singular handling
        exact_match = None
        partial_matches = []
        
        query_lower = query_product.lower()
        # Handle plural/singular variations
        query_variations = [query_lower]
        if query_lower.endswith('s') and len(query_lower) > 3:
            query_variations.append(query_lower[:-1])  # Remove 's' for singular
        if not query_lower.endswith('s'):
            query_variations.append(query_lower + 's')  # Add 's' for plural
        
        for product in products:
            product_name_lower = product['name'].lower()
            
            # Check if any query variation matches the product name
            is_match = False
            for variation in query_variations:
                if (variation in product_name_lower or 
                    product_name_lower in variation or
                    any(word in product_name_lower for word in variation.split()) or
                    any(word in variation for word in product_name_lower.split())):
                    is_match = True
                    break
            
            if is_match:
                if len(product_name_lower.split()) <= 3:  # Prefer shorter, more exact matches
                    if exact_match is None or len(product['name']) < len(exact_match['name']):
                        exact_match = product
                else:
                    partial_matches.append(product)
        
        if exact_match:
            stock = exact_match['stock_quantity']
            name = exact_match['name']
            price = exact_match['price']
            currency = exact_match.get('currency', 'TND')
            
            if stock == 0:
                response = f"I'm sorry, but we're currently out of stock for the **{name}**. "
                # Suggest alternatives from partial matches or similar category
                if partial_matches:
                    response += f"However, you might be interested in these similar items:\n\n"
                    for product in partial_matches[:2]:
                        response += f"• **{product['name']}** - {product['price']} {product.get('currency', 'TND')} (Stock: {product['stock_quantity']})\n"
                else:
                    response += "Would you like me to show you our other available products?"
            elif stock <= 5:
                response = f"We have the **{name}** for {price} {currency}, but not many left - only **{stock} remaining** in stock! "
                response += "I'd recommend ordering soon if you're interested. 😊"
            else:
                response = f"Good news! We have **{stock} {name}** in stock for {price} {currency} each. "
                response += "Plenty available for your order! 🎉"
            
            return response
        
        elif partial_matches:
            response = f"I found these products related to '{query_product}':\n\n"
            for product in partial_matches[:3]:
                stock = product['stock_quantity']
                stock_text = "In Stock" if stock > 0 else "Out of Stock"
                if stock > 0 and stock <= 5:
                    stock_text = f"Only {stock} left!"
                response += f"• **{product['name']}** - {product['price']} {product.get('currency', 'TND')} ({stock_text})\n"
            
            return response
        
        else:
            return f"I couldn't find any products matching '{query_product}'. Would you like me to show you our full collection instead?"
    
    def _format_detailed_product_info(self, product: Dict[str, Any]) -> str:
        """Format detailed information about a specific product"""
        name = product['name']
        price = product['price']
        currency = product.get('currency', 'TND')
        description = product.get('description', '')
        stock = product['stock_quantity']
        category = product.get('category', '')
        
        response = f"## **{name}** ✨\n"
        response += f"💰 **Price:** {price} {currency}\n"
        response += f"📦 **Stock:** {stock} units available\n"
        
        if category:
            response += f"🏷️ **Category:** {category}\n"
        
        if description:
            response += f"\n📝 **Description:**\n{description}\n"
        
        # Add specific details based on product type
        if "robe" in name.lower() or "kaftan" in name.lower():
            response += f"\n✨ **Perfect for:**\n"
            response += f"• Special occasions and celebrations\n"
            response += f"• Traditional Tunisian events\n"
            response += f"• Elegant evening wear\n"
            response += f"• Cultural appreciation\n"
            
            response += f"\n🎨 **Craftsmanship:**\n"
            response += f"• Handcrafted by skilled Tunisian artisans\n"
            response += f"• Traditional embroidery techniques\n"
            response += f"• Authentic Tunisian heritage\n"
            response += f"• High-quality materials and attention to detail\n"
        
        if stock > 0:
            if stock <= 5:
                response += f"\n⚠️ **Limited stock!** Only {stock} left - order soon!"
            else:
                response += f"\n✅ **In stock and ready to ship!**"
            
            response += f"\n💝 Would you like to know more about sizing, shipping, or have any other questions about the **{name}**?"
        else:
            response += f"\n❌ **Currently out of stock** - but we're expecting new inventory soon!"
        
        return response

    def _prepare_product_context_for_llm(self, products: List[Dict[str, Any]], search_term: str) -> str:
        """Prepare product information as context for the main LLM to use in its response"""
        if not products:
            return f"PRODUCT_CONTEXT: No products found for '{search_term}'. We have other traditional Tunisian items available."
        
        context = f"PRODUCT_CONTEXT: Found {len(products)} product(s) for '{search_term}':\n"
        
        for i, product in enumerate(products[:3], 1):  # Limit to top 3 results
            context += f"\n{i}. **{product['name']}**\n"
            context += f"   - Price: {product['price']} {product.get('currency', 'TND')}\n"
            context += f"   - Stock: {product['stock_quantity']} units\n"
            context += f"   - Description: {product.get('description', 'No description')}\n"
            context += f"   - Category: {product.get('category', 'Uncategorized')}\n"
        
        if len(products) > 3:
            context += f"\n(And {len(products) - 3} more products available)\n"
            
        context += "\nUSE_THIS_INFO: Use this product information to provide a helpful, natural response about our available items."
        return context
    
    def _prepare_stock_context_for_llm(self, products: List[Dict[str, Any]], product_name: str) -> str:
        """Prepare stock information as context for the main LLM"""
        if not products:
            return f"STOCK_CONTEXT: No stock information found for '{product_name}'. Product may not exist or be out of stock."
        
        context = f"STOCK_CONTEXT: Stock information for '{product_name}':\n"
        
        for product in products[:3]:  # Top 3 matches
            stock = product['stock_quantity']
            context += f"\n- **{product['name']}**: {stock} units in stock"
            context += f" (Price: {product['price']} {product.get('currency', 'TND')})\n"
            
            if stock == 0:
                context += "  Status: OUT OF STOCK\n"
            elif stock <= 5:
                context += "  Status: LIMITED STOCK - recommend ordering soon\n"
            else:
                context += "  Status: GOOD AVAILABILITY\n"
        
        context += "\nUSE_THIS_INFO: Use this stock information to provide accurate availability details."
        return context
    
    def _prepare_detailed_context_for_llm(self, products: List[Dict[str, Any]], product_name: str) -> str:
        """Prepare detailed product information as context for the main LLM"""
        if not products:
            return f"PRODUCT_DETAILS: No detailed information found for '{product_name}'."
        
        # Use the best match (first product)
        product = products[0]
        
        context = f"PRODUCT_DETAILS: Detailed information for {product['name']}:\n"
        context += f"- Price: {product['price']} {product.get('currency', 'TND')}\n"
        context += f"- Stock: {product['stock_quantity']} units available\n"
        context += f"- Category: {product.get('category', 'Traditional Wear')}\n"
        context += f"- Description: {product.get('description', 'Traditional Tunisian artisanat piece')}\n"
        
        # Add specific context based on product type
        if "robe" in product['name'].lower() or "carthagean" in product['name'].lower():
            context += "\nSUITABILITY_INFO:\n"
            context += "- PERFECT FOR: Weddings, formal events, special occasions, cultural celebrations\n"
            context += "- STYLE: Traditional formal wear with intricate embroidery\n"
            context += "- OCCASION_LEVEL: Very formal and elegant\n"
            context += "- CULTURAL_SIGNIFICANCE: Traditional Tunisian formal attire\n"
        elif "kaftan" in product['name'].lower():
            context += "\nSUITABILITY_INFO:\n"
            context += "- PERFECT FOR: Both formal and casual occasions, very versatile\n"
            context += "- STYLE: Comfortable yet elegant flowing design\n"
            context += "- OCCASION_LEVEL: Can be dressed up or down\n"
        
        context += "\nUSE_THIS_INFO: Use this detailed information to answer questions about suitability, features, or characteristics."
        return context
    
    def _add_product_context_to_conversation(self, session_id: str, context: str):
        """Add product context to conversation memory for the LLM to use"""
        self._add_to_conversation(session_id, "system", context)

# Global chatbot agent instance
chatbot_agent = ChatbotAgent()
