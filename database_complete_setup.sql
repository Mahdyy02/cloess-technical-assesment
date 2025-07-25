-- CLOESS Database Setup Script
-- Complete database schema for CLOESS Tunisian Fashion E-commerce Platform
-- Run this script in your PostgreSQL database after creating the 'cloess' database

-- Connect to the cloess database first
-- \c cloess;

-- Products table - Main product catalog
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'TND',
    description TEXT,
    image_url TEXT,
    category VARCHAR(100),
    stock_quantity INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User sessions table for analytics - IP-based user tracking
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL UNIQUE,
    country VARCHAR(100),
    city VARCHAR(100),
    region VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    user_agent TEXT,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_session_time_ms BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Product interactions table for analytics - Tracks user behavior per product
CREATE TABLE IF NOT EXISTS product_interactions (
    id SERIAL PRIMARY KEY,
    user_session_id INTEGER REFERENCES user_sessions(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    total_hover_time_ms BIGINT DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    first_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_session_id, product_id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_user_sessions_ip ON user_sessions(ip_address);
CREATE INDEX IF NOT EXISTS idx_user_sessions_country ON user_sessions(country);
CREATE INDEX IF NOT EXISTS idx_product_interactions_user_product ON product_interactions(user_session_id, product_id);
CREATE INDEX IF NOT EXISTS idx_product_interactions_product ON product_interactions(product_id);
CREATE INDEX IF NOT EXISTS idx_product_interactions_last ON product_interactions(last_interaction);

-- Update trigger function for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to all tables
CREATE TRIGGER update_products_updated_at 
    BEFORE UPDATE ON products 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_sessions_updated_at 
    BEFORE UPDATE ON user_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_interactions_updated_at 
    BEFORE UPDATE ON product_interactions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample product data
INSERT INTO products (name, price, description, image_url, category, stock_quantity) VALUES
('Traditional Tunisian Robe', 89.99, 'Elegant traditional Tunisian robe made from premium fabrics with intricate embroidery', '/images/robe1.jpg', 'Traditional Wear', 15),
('Modern Tunisian Dress', 65.50, 'Contemporary dress with traditional Tunisian patterns and modern styling', '/images/dress1.jpg', 'Modern Wear', 22),
('Handwoven Scarf', 29.99, 'Beautiful handwoven scarf with authentic Tunisian designs and vibrant colors', '/images/scarf1.jpg', 'Accessories', 30),
('Traditional Kaftan', 120.00, 'Luxurious kaftan perfect for special occasions with gold thread detailing', '/images/kaftan1.jpg', 'Traditional Wear', 8),
('Embroidered Tunic', 55.75, 'Comfortable tunic with intricate embroidery work and flowing silhouette', '/images/tunic1.jpg', 'Casual Wear', 18),
('Berber Jewelry Set', 85.00, 'Authentic Berber jewelry set with traditional silver work', '/images/jewelry1.jpg', 'Accessories', 12),
('Modern Abaya', 95.25, 'Contemporary abaya with modern cuts and traditional elements', '/images/abaya1.jpg', 'Modern Wear', 16),
('Traditional Vest', 45.00, 'Classic Tunisian vest with traditional patterns and comfortable fit', '/images/vest1.jpg', 'Traditional Wear', 25),
('Casual Tunic', 42.99, 'Everyday tunic with subtle traditional motifs perfect for daily wear', '/images/tunic2.jpg', 'Casual Wear', 20),
('Evening Dress', 135.00, 'Elegant evening dress combining modern design with Tunisian heritage', '/images/evening1.jpg', 'Formal Wear', 6);

-- Verify the setup
SELECT 'Database setup completed successfully!' as status;
SELECT 'Products table' as table_name, COUNT(*) as record_count FROM products
UNION ALL
SELECT 'User sessions table' as table_name, COUNT(*) as record_count FROM user_sessions
UNION ALL
SELECT 'Product interactions table' as table_name, COUNT(*) as record_count FROM product_interactions;
