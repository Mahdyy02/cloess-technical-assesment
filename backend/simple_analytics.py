import asyncpg
import httpx
from typing import Dict, List, Any, Optional

class SimpleAnalyticsManager:
    """Simple analytics manager for tracking user interactions without complex UI"""
    
    def __init__(self, db_pool):
        self.pool = db_pool
    
    async def get_user_location(self, ip_address: str) -> Dict[str, Any]:
        """Get location data for IP address"""
        if ip_address in ['127.0.0.1', 'localhost', '::1']:
            return {
                'country': 'Tunisia',
                'city': 'Tunis',
                'region': 'Tunis',
                'latitude': 36.8190,
                'longitude': 10.1658
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'http://ip-api.com/json/{ip_address}?fields=status,country,regionName,city,lat,lon',
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        return {
                            'country': data.get('country'),
                            'city': data.get('city'),
                            'region': data.get('regionName'),
                            'latitude': data.get('lat'),
                            'longitude': data.get('lon')
                        }
        except Exception as e:
            print(f"Geolocation error: {e}")
        
        return {
            'country': 'Unknown',
            'city': 'Unknown',
            'region': 'Unknown',
            'latitude': None,
            'longitude': None
        }
    
    async def track_user_session(self, ip_address: str, user_agent: str = '') -> int:
        """Get or create user session"""
        async with self.pool.acquire() as conn:
            # Check if user exists
            user = await conn.fetchrow(
                "SELECT id FROM user_sessions WHERE ip_address = $1",
                ip_address
            )
            
            if user:
                # Update last seen
                await conn.execute(
                    "UPDATE user_sessions SET last_seen = CURRENT_TIMESTAMP WHERE id = $1",
                    user['id']
                )
                return user['id']
            else:
                # Create new user
                location = await self.get_user_location(ip_address)
                
                user_id = await conn.fetchval("""
                    INSERT INTO user_sessions (
                        ip_address, country, city, region, 
                        latitude, longitude, user_agent
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """, 
                    ip_address,
                    location['country'],
                    location['city'], 
                    location['region'],
                    location['latitude'],
                    location['longitude'],
                    user_agent
                )
                return user_id
    
    async def track_product_interaction(
        self, 
        user_session_id: int, 
        product_id: int, 
        interaction_type: str,
        duration_ms: Optional[int] = None,
        page_url: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Track product interactions - accumulate data per user/product"""
        async with self.pool.acquire() as conn:
            # Get existing interaction record
            existing = await conn.fetchrow("""
                SELECT id, total_hover_time_ms, total_views, total_clicks 
                FROM product_interactions 
                WHERE user_session_id = $1 AND product_id = $2
            """, user_session_id, product_id)
            
            if existing:
                # Update existing record
                if interaction_type == 'hover' and duration_ms:
                    # Add to total hover time
                    new_hover_time = (existing['total_hover_time_ms'] or 0) + duration_ms
                    await conn.execute("""
                        UPDATE product_interactions 
                        SET total_hover_time_ms = $1, last_interaction = CURRENT_TIMESTAMP
                        WHERE id = $2
                    """, new_hover_time, existing['id'])
                    
                elif interaction_type == 'view':
                    # Only count first view per user/product combination
                    if existing['total_views'] == 0:
                        await conn.execute("""
                            UPDATE product_interactions 
                            SET total_views = 1, last_interaction = CURRENT_TIMESTAMP
                            WHERE id = $1
                        """, existing['id'])
                        
                elif interaction_type == 'click':
                    # Increment click count
                    new_clicks = (existing['total_clicks'] or 0) + 1
                    await conn.execute("""
                        UPDATE product_interactions 
                        SET total_clicks = $1, last_interaction = CURRENT_TIMESTAMP
                        WHERE id = $2
                    """, new_clicks, existing['id'])
            else:
                # Create new interaction record
                hover_time = duration_ms if interaction_type == 'hover' else 0
                views = 1 if interaction_type == 'view' else 0
                clicks = 1 if interaction_type == 'click' else 0
                
                await conn.execute("""
                    INSERT INTO product_interactions (
                        user_session_id, product_id, total_hover_time_ms, 
                        total_views, total_clicks
                    ) VALUES ($1, $2, $3, $4, $5)
                """, user_session_id, product_id, hover_time, views, clicks)
    
    async def get_user_analytics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user analytics data"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    us.ip_address,
                    us.country,
                    us.city,
                    us.first_seen,
                    us.last_seen,
                    COALESCE(SUM(pi.total_hover_time_ms), 0) as total_hover_time,
                    COALESCE(SUM(pi.total_views), 0) as total_views,
                    COALESCE(SUM(pi.total_clicks), 0) as total_clicks,
                    COUNT(DISTINCT pi.product_id) as products_interacted
                FROM user_sessions us
                LEFT JOIN product_interactions pi ON us.id = pi.user_session_id
                GROUP BY us.id, us.ip_address, us.country, us.city, us.first_seen, us.last_seen
                ORDER BY us.last_seen DESC
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]
    
    async def get_product_analytics(self, product_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get product analytics data"""
        async with self.pool.acquire() as conn:
            if product_id:
                rows = await conn.fetch("""
                    SELECT 
                        pi.product_id,
                        COUNT(DISTINCT pi.user_session_id) as unique_users,
                        COALESCE(SUM(pi.total_hover_time_ms), 0) as total_hover_time,
                        COALESCE(SUM(pi.total_views), 0) as total_views,
                        COALESCE(SUM(pi.total_clicks), 0) as total_clicks,
                        COALESCE(AVG(pi.total_hover_time_ms), 0) as avg_hover_time
                    FROM product_interactions pi
                    WHERE pi.product_id = $1
                    GROUP BY pi.product_id
                """, product_id)
            else:
                rows = await conn.fetch("""
                    SELECT 
                        pi.product_id,
                        COUNT(DISTINCT pi.user_session_id) as unique_users,
                        COALESCE(SUM(pi.total_hover_time_ms), 0) as total_hover_time,
                        COALESCE(SUM(pi.total_views), 0) as total_views,
                        COALESCE(SUM(pi.total_clicks), 0) as total_clicks,
                        COALESCE(AVG(pi.total_hover_time_ms), 0) as avg_hover_time
                    FROM product_interactions pi
                    GROUP BY pi.product_id
                    ORDER BY total_hover_time DESC
                """)
            
            return [dict(row) for row in rows]
    
    async def get_country_analytics(self) -> List[Dict[str, Any]]:
        """Get analytics by country"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    us.country,
                    COUNT(DISTINCT us.id) as user_count,
                    COALESCE(SUM(pi.total_hover_time_ms), 0) as total_hover_time,
                    COALESCE(SUM(pi.total_views), 0) as total_views,
                    COALESCE(SUM(pi.total_clicks), 0) as total_clicks
                FROM user_sessions us
                LEFT JOIN product_interactions pi ON us.id = pi.user_session_id
                WHERE us.country IS NOT NULL AND us.country != 'Unknown'
                GROUP BY us.country
                ORDER BY user_count DESC
            """)
            
            return [dict(row) for row in rows]
