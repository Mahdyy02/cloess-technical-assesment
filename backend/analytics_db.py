import os
import asyncpg
import httpx
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Database configuration (same as main database)
DATABASE_CONFIG = {
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "cloess"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

class AnalyticsManager:
    """Manager for user analytics and product interaction tracking"""
    
    def __init__(self, db_pool):
        self.pool = db_pool
    
    async def create_analytics_tables(self):
        """Create analytics tables if they don't exist"""
        try:
            async with self.pool.acquire() as connection:
                # Create user_sessions table
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id SERIAL PRIMARY KEY,
                        ip_address INET NOT NULL,
                        country VARCHAR(100),
                        country_code VARCHAR(2),
                        region VARCHAR(100),
                        city VARCHAR(100),
                        latitude DECIMAL(10, 8),
                        longitude DECIMAL(11, 8),
                        timezone VARCHAR(50),
                        isp VARCHAR(200),
                        user_agent TEXT,
                        first_visit TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        last_visit TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        visit_count INTEGER DEFAULT 1,
                        total_session_duration INTEGER DEFAULT 0, -- in seconds
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(ip_address)
                    );
                """)
                
                # Create product_interactions table
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS product_interactions (
                        id SERIAL PRIMARY KEY,
                        user_session_id INTEGER REFERENCES user_sessions(id) ON DELETE CASCADE,
                        product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                        interaction_type VARCHAR(50) NOT NULL, -- 'hover', 'click', 'view'
                        duration_ms INTEGER, -- duration in milliseconds for hover events
                        interaction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        page_url TEXT,
                        session_id VARCHAR(100), -- frontend session ID
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create indexes for better performance
                await connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_sessions_ip ON user_sessions(ip_address);
                    CREATE INDEX IF NOT EXISTS idx_product_interactions_user_product 
                        ON product_interactions(user_session_id, product_id);
                    CREATE INDEX IF NOT EXISTS idx_product_interactions_timestamp 
                        ON product_interactions(interaction_timestamp);
                    CREATE INDEX IF NOT EXISTS idx_product_interactions_product 
                        ON product_interactions(product_id);
                """)
                
                print("✅ Analytics tables created successfully")
                
        except Exception as e:
            print(f"❌ Error creating analytics tables: {e}")
            raise
    
    async def get_ip_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Get geolocation data for an IP address using a free API"""
        try:
            # Skip geolocation for localhost/private IPs
            if ip_address in ['127.0.0.1', 'localhost'] or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
                return {
                    'country': 'Local',
                    'country_code': 'LCL',
                    'region': 'Local',
                    'city': 'Local',
                    'latitude': 0.0,
                    'longitude': 0.0,
                    'timezone': 'UTC',
                    'isp': 'Local Network'
                }
            
            # Use ip-api.com (free, no API key required, 1000 requests/hour)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,region,city,lat,lon,timezone,isp",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        return {
                            'country': data.get('country', 'Unknown'),
                            'country_code': data.get('countryCode', 'XX'),
                            'region': data.get('region', 'Unknown'),
                            'city': data.get('city', 'Unknown'),
                            'latitude': float(data.get('lat', 0)) if data.get('lat') else 0.0,
                            'longitude': float(data.get('lon', 0)) if data.get('lon') else 0.0,
                            'timezone': data.get('timezone', 'UTC'),
                            'isp': data.get('isp', 'Unknown')
                        }
                
        except Exception as e:
            print(f"Warning: Could not get geolocation for IP {ip_address}: {e}")
        
        # Fallback data
        return {
            'country': 'Unknown',
            'country_code': 'XX',
            'region': 'Unknown',
            'city': 'Unknown',
            'latitude': 0.0,
            'longitude': 0.0,
            'timezone': 'UTC',
            'isp': 'Unknown'
        }
    
    async def track_user_session(self, ip_address: str, user_agent: str = None) -> int:
        """Track user session and return user_session_id"""
        try:
            async with self.pool.acquire() as connection:
                # Check if user session already exists
                existing_session = await connection.fetchrow(
                    "SELECT id, visit_count FROM user_sessions WHERE ip_address = $1",
                    ip_address
                )
                
                if existing_session:
                    # Update existing session
                    await connection.execute("""
                        UPDATE user_sessions 
                        SET last_visit = CURRENT_TIMESTAMP,
                            visit_count = visit_count + 1,
                            updated_at = CURRENT_TIMESTAMP,
                            user_agent = COALESCE($2, user_agent)
                        WHERE ip_address = $1
                    """, ip_address, user_agent)
                    return existing_session['id']
                else:
                    # Create new session with geolocation data
                    geo_data = await self.get_ip_geolocation(ip_address)
                    
                    user_session_id = await connection.fetchval("""
                        INSERT INTO user_sessions (
                            ip_address, country, country_code, region, city,
                            latitude, longitude, timezone, isp, user_agent
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        RETURNING id
                    """, 
                        ip_address,
                        geo_data['country'],
                        geo_data['country_code'],
                        geo_data['region'],
                        geo_data['city'],
                        geo_data['latitude'],
                        geo_data['longitude'],
                        geo_data['timezone'],
                        geo_data['isp'],
                        user_agent
                    )
                    return user_session_id
                    
        except Exception as e:
            print(f"Error tracking user session: {e}")
            raise
    
    async def track_product_interaction(
        self, 
        user_session_id: int, 
        product_id: int, 
        interaction_type: str,
        duration_ms: int = None,
        page_url: str = None,
        session_id: str = None
    ):
        """Track product interaction (hover, click, view)"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    INSERT INTO product_interactions (
                        user_session_id, product_id, interaction_type, 
                        duration_ms, page_url, session_id
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, user_session_id, product_id, interaction_type, duration_ms, page_url, session_id)
                
        except Exception as e:
            print(f"Error tracking product interaction: {e}")
            # Don't raise exception for analytics errors - shouldn't break main functionality
    
    async def get_user_analytics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user analytics summary"""
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch("""
                    SELECT 
                        us.ip_address,
                        us.country,
                        us.city,
                        us.visit_count,
                        us.first_visit,
                        us.last_visit,
                        us.total_session_duration,
                        COUNT(pi.id) as total_interactions,
                        COUNT(DISTINCT pi.product_id) as unique_products_viewed
                    FROM user_sessions us
                    LEFT JOIN product_interactions pi ON us.id = pi.user_session_id
                    GROUP BY us.id, us.ip_address, us.country, us.city, 
                             us.visit_count, us.first_visit, us.last_visit, us.total_session_duration
                    ORDER BY us.last_visit DESC
                    LIMIT $1
                """, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error getting user analytics: {e}")
            return []
    
    async def get_product_analytics(self, product_id: int = None) -> List[Dict[str, Any]]:
        """Get product interaction analytics"""
        try:
            async with self.pool.acquire() as connection:
                if product_id:
                    # Analytics for specific product
                    rows = await connection.fetch("""
                        SELECT 
                            p.name as product_name,
                            COUNT(pi.id) as total_interactions,
                            COUNT(DISTINCT pi.user_session_id) as unique_users,
                            AVG(pi.duration_ms) as avg_hover_duration_ms,
                            SUM(CASE WHEN pi.interaction_type = 'hover' THEN 1 ELSE 0 END) as hover_count,
                            SUM(CASE WHEN pi.interaction_type = 'click' THEN 1 ELSE 0 END) as click_count,
                            SUM(CASE WHEN pi.interaction_type = 'view' THEN 1 ELSE 0 END) as view_count
                        FROM products p
                        LEFT JOIN product_interactions pi ON p.id = pi.product_id
                        WHERE p.id = $1
                        GROUP BY p.id, p.name
                    """, product_id)
                else:
                    # Analytics for all products
                    rows = await connection.fetch("""
                        SELECT 
                            p.id as product_id,
                            p.name as product_name,
                            COUNT(pi.id) as total_interactions,
                            COUNT(DISTINCT pi.user_session_id) as unique_users,
                            AVG(pi.duration_ms) as avg_hover_duration_ms,
                            SUM(CASE WHEN pi.interaction_type = 'hover' THEN 1 ELSE 0 END) as hover_count,
                            SUM(CASE WHEN pi.interaction_type = 'click' THEN 1 ELSE 0 END) as click_count,
                            SUM(CASE WHEN pi.interaction_type = 'view' THEN 1 ELSE 0 END) as view_count
                        FROM products p
                        LEFT JOIN product_interactions pi ON p.id = pi.product_id
                        GROUP BY p.id, p.name
                        ORDER BY total_interactions DESC
                    """)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error getting product analytics: {e}")
            return []
    
    async def get_country_analytics(self) -> List[Dict[str, Any]]:
        """Get analytics by country"""
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch("""
                    SELECT 
                        us.country,
                        us.country_code,
                        COUNT(DISTINCT us.id) as unique_users,
                        SUM(us.visit_count) as total_visits,
                        COUNT(pi.id) as total_interactions,
                        AVG(pi.duration_ms) as avg_interaction_duration_ms
                    FROM user_sessions us
                    LEFT JOIN product_interactions pi ON us.id = pi.user_session_id
                    GROUP BY us.country, us.country_code
                    ORDER BY unique_users DESC
                """)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"Error getting country analytics: {e}")
            return []

# Global analytics manager (will be initialized with db pool)
analytics_manager = None

def initialize_analytics(db_pool):
    """Initialize analytics manager with database pool"""
    global analytics_manager
    analytics_manager = AnalyticsManager(db_pool)
    return analytics_manager
