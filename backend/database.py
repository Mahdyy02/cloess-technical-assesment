import os
import asyncpg
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_CONFIG = {
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),  # Empty default to force explicit setting
    "database": os.getenv("DB_NAME", "cloess"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

DATABASE_URL = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.analytics_manager = None

    async def create_pool(self):
        """Create a connection pool"""
        try:
            # Validate configuration
            if not DATABASE_CONFIG["password"]:
                raise Exception("Database password not configured. Please set DB_PASSWORD environment variable.")
            
            print(f"🔗 Attempting to connect to database...")
            print(f"   Host: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
            print(f"   Database: {DATABASE_CONFIG['database']}")
            print(f"   User: {DATABASE_CONFIG['user']}")
            
            # Test connection first
            try:
                test_conn = await asyncpg.connect(
                    user=DATABASE_CONFIG["user"],
                    password=DATABASE_CONFIG["password"],
                    database=DATABASE_CONFIG["database"],
                    host=DATABASE_CONFIG["host"],
                    port=DATABASE_CONFIG["port"],
                    timeout=10
                )
                await test_conn.close()
                print("✅ Test connection successful")
            except Exception as test_error:
                print(f"❌ Test connection failed: {test_error}")
                raise

            self.pool = await asyncpg.create_pool(
                user=DATABASE_CONFIG["user"],
                password=DATABASE_CONFIG["password"],
                database=DATABASE_CONFIG["database"],
                host=DATABASE_CONFIG["host"],
                port=DATABASE_CONFIG["port"],
                min_size=1,
                max_size=10,
                timeout=10,
                command_timeout=5
            )
            print("✅ Database connection pool created successfully")
            
            # Initialize analytics manager
            from analytics_db import initialize_analytics
            self.analytics_manager = initialize_analytics(self.pool)
            await self.analytics_manager.create_analytics_tables()
            
        except Exception as e:
            print(f"❌ Failed to create database pool: {e}")
            print("💡 Troubleshooting tips:")
            print("   1. Check if PostgreSQL is running")
            print("   2. Verify your password in .env file")
            print("   3. Ensure the 'cloess' database exists")
            print("   4. Check pg_hba.conf for authentication settings")
            raise
        except Exception as e:
            print(f"❌ Failed to create database pool: {e}")
            print("💡 Troubleshooting tips:")
            print("   1. Check if PostgreSQL is running")
            print("   2. Verify your password in .env file")
            print("   3. Ensure the 'cloess' database exists")
            print("   4. Check pg_hba.conf for authentication settings")
            raise

    async def close_pool(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            print("Database connection pool closed")

    async def get_products(self, category: str = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch products from database"""
        if not self.pool:
            raise Exception("Database pool not initialized")

        try:
            async with self.pool.acquire() as connection:
                if category:
                    query = """
                        SELECT id, name, price, currency, description, image_url, category, stock_quantity
                        FROM products 
                        WHERE is_active = true AND category = $1
                        ORDER BY created_at DESC
                        LIMIT $2 OFFSET $3
                    """
                    rows = await connection.fetch(query, category, limit, offset)
                else:
                    query = """
                        SELECT id, name, price, currency, description, image_url, category, stock_quantity
                        FROM products 
                        WHERE is_active = true
                        ORDER BY created_at DESC
                        LIMIT $1 OFFSET $2
                    """
                    rows = await connection.fetch(query, limit, offset)

                # Convert rows to list of dictionaries
                products = []
                for row in rows:
                    product = {
                        "id": row["id"],
                        "name": row["name"],
                        "price": float(row["price"]),
                        "currency": row["currency"],
                        "description": row["description"],
                        "image_url": row["image_url"],
                        "category": row["category"],
                        "stock_quantity": row["stock_quantity"]
                    }
                    products.append(product)

                return products

        except Exception as e:
            print(f"Error fetching products: {e}")
            raise

    async def get_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """Fetch a single product by ID"""
        if not self.pool:
            raise Exception("Database pool not initialized")

        try:
            async with self.pool.acquire() as connection:
                query = """
                    SELECT id, name, price, currency, description, image_url, category, stock_quantity
                    FROM products 
                    WHERE id = $1 AND is_active = true
                """
                row = await connection.fetchrow(query, product_id)
                
                if row:
                    return {
                        "id": row["id"],
                        "name": row["name"],
                        "price": float(row["price"]),
                        "currency": row["currency"],
                        "description": row["description"],
                        "image_url": row["image_url"],
                        "category": row["category"],
                        "stock_quantity": row["stock_quantity"]
                    }
                return None

        except Exception as e:
            print(f"Error fetching product: {e}")
            raise

    async def get_categories(self) -> List[str]:
        """Fetch all product categories"""
        if not self.pool:
            raise Exception("Database pool not initialized")

        try:
            async with self.pool.acquire() as connection:
                query = """
                    SELECT DISTINCT category 
                    FROM products 
                    WHERE is_active = true AND category IS NOT NULL
                    ORDER BY category
                """
                rows = await connection.fetch(query)
                return [row["category"] for row in rows]

        except Exception as e:
            print(f"Error fetching categories: {e}")
            raise

    async def search_products(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search products by name, description, or category"""
        if not self.pool:
            raise Exception("Database pool not initialized")

        try:
            async with self.pool.acquire() as connection:
                query = """
                    SELECT id, name, price, currency, description, image_url, category, stock_quantity
                    FROM products 
                    WHERE is_active = true AND (
                        name ILIKE $1 OR 
                        description ILIKE $1 OR 
                        category ILIKE $1
                    )
                    ORDER BY 
                        CASE 
                            WHEN LOWER(name) = LOWER($2) THEN 1
                            WHEN name ILIKE $1 THEN 2
                            WHEN description ILIKE $1 THEN 3
                            ELSE 4 
                        END,
                        created_at DESC
                    LIMIT $3
                """
                search_pattern = f"%{search_term}%"
                rows = await connection.fetch(query, search_pattern, search_term, limit)

                products = []
                for row in rows:
                    product = {
                        "id": row["id"],
                        "name": row["name"],
                        "price": float(row["price"]),
                        "currency": row["currency"],
                        "description": row["description"],
                        "image_url": row["image_url"],
                        "category": row["category"],
                        "stock_quantity": row["stock_quantity"]
                    }
                    products.append(product)

                return products

        except Exception as e:
            print(f"Error searching products: {e}")
            return []

    async def get_products_by_price_range(self, min_price: float = None, max_price: float = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get products within a price range"""
        if not self.pool:
            raise Exception("Database pool not initialized")

        try:
            async with self.pool.acquire() as connection:
                conditions = ["is_active = true"]
                params = []
                param_count = 0

                if min_price is not None:
                    param_count += 1
                    conditions.append(f"price >= ${param_count}")
                    params.append(min_price)

                if max_price is not None:
                    param_count += 1
                    conditions.append(f"price <= ${param_count}")
                    params.append(max_price)

                param_count += 1
                params.append(limit)

                query = f"""
                    SELECT id, name, price, currency, description, image_url, category, stock_quantity
                    FROM products 
                    WHERE {' AND '.join(conditions)}
                    ORDER BY price ASC
                    LIMIT ${param_count}
                """

                rows = await connection.fetch(query, *params)

                products = []
                for row in rows:
                    product = {
                        "id": row["id"],
                        "name": row["name"],
                        "price": float(row["price"]),
                        "currency": row["currency"],
                        "description": row["description"],
                        "image_url": row["image_url"],
                        "category": row["category"],
                        "stock_quantity": row["stock_quantity"]
                    }
                    products.append(product)

                return products

        except Exception as e:
            print(f"Error fetching products by price: {e}")
            raise

    async def get_product_stats(self) -> Dict[str, Any]:
        """Get product statistics for the chatbot"""
        if not self.pool:
            raise Exception("Database pool not initialized")

        try:
            async with self.pool.acquire() as connection:
                # Get various statistics
                stats_query = """
                    SELECT 
                        COUNT(*) as total_products,
                        COUNT(DISTINCT category) as total_categories,
                        MIN(price) as min_price,
                        MAX(price) as max_price,
                        AVG(price) as avg_price,
                        SUM(stock_quantity) as total_stock
                    FROM products 
                    WHERE is_active = true
                """
                stats = await connection.fetchrow(stats_query)

                # Get category breakdown
                category_query = """
                    SELECT category, COUNT(*) as count, AVG(price) as avg_price
                    FROM products 
                    WHERE is_active = true AND category IS NOT NULL
                    GROUP BY category
                    ORDER BY count DESC
                """
                categories = await connection.fetch(category_query)

                return {
                    "total_products": stats["total_products"],
                    "total_categories": stats["total_categories"],
                    "price_range": {
                        "min": float(stats["min_price"]) if stats["min_price"] else 0,
                        "max": float(stats["max_price"]) if stats["max_price"] else 0,
                        "average": float(stats["avg_price"]) if stats["avg_price"] else 0
                    },
                    "total_stock": stats["total_stock"],
                    "categories": [
                        {
                            "name": cat["category"],
                            "count": cat["count"],
                            "avg_price": float(cat["avg_price"])
                        }
                        for cat in categories
                    ]
                }

        except Exception as e:
            print(f"Error fetching product stats: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()
