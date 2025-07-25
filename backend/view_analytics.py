import asyncio
import asyncpg
from simple_analytics import SimpleAnalyticsManager
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_CONFIG = {
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "cloess"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

async def view_analytics():
    """Simple script to view analytics data from command line"""
    
    # Create database connection
    pool = await asyncpg.create_pool(**DATABASE_CONFIG)
    analytics = SimpleAnalyticsManager(pool)
    
    print("=" * 60)
    print("CLOESS ANALYTICS DASHBOARD")
    print("=" * 60)
    
    try:
        # Get user analytics
        users = await analytics.get_user_analytics(limit=20)
        print(f"\n📊 USER ANALYTICS ({len(users)} users)")
        print("-" * 50)
        for user in users[:10]:  # Show top 10
            print(f"IP: {user['ip_address']} | Country: {user['country']} | City: {user['city']}")
            print(f"   Hover Time: {user['total_hover_time']/1000:.1f}s | Views: {user['total_views']} | Clicks: {user['total_clicks']}")
            print(f"   Products: {user['products_interacted']} | Last Seen: {user['last_seen']}")
            print()
        
        # Get product analytics
        products = await analytics.get_product_analytics()
        print(f"\n🛍️  PRODUCT ANALYTICS ({len(products)} products)")
        print("-" * 50)
        for product in products[:10]:  # Show top 10
            print(f"Product ID: {product['product_id']} | Users: {product['unique_users']}")
            print(f"   Total Hover: {product['total_hover_time']/1000:.1f}s | Avg: {product['avg_hover_time']/1000:.1f}s")
            print(f"   Views: {product['total_views']} | Clicks: {product['total_clicks']}")
            print()
        
        # Get country analytics
        countries = await analytics.get_country_analytics()
        print(f"\n🌍 COUNTRY ANALYTICS ({len(countries)} countries)")
        print("-" * 50)
        for country in countries:
            print(f"{country['country']}: {country['user_count']} users")
            print(f"   Total Hover: {country['total_hover_time']/1000:.1f}s | Views: {country['total_views']} | Clicks: {country['total_clicks']}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(view_analytics())
