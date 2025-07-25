import React, { useState, useRef, useEffect } from 'react';

/**
 * Product Grid with Hover Analytics
 * Tracks hover duration for each product and sends analytics data
 */

// Hook for analytics tracking
const useProductAnalytics = (apiBaseUrl = 'http://localhost:8000') => {
    const [isInitialized, setIsInitialized] = useState(false);
    const sessionId = useRef(`session_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`);

    useEffect(() => {
        // Initialize session tracking
        const initSession = async () => {
            try {
                await fetch(`${apiBaseUrl}/analytics/session`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                setIsInitialized(true);
                console.log('✅ Analytics session initialized');
            } catch (error) {
                console.warn('Failed to initialize analytics:', error);
            }
        };
        initSession();
    }, [apiBaseUrl]);

    const trackInteraction = async (productId, interactionType, durationMs = null) => {
        if (!isInitialized) return;

        try {
            await fetch(`${apiBaseUrl}/analytics/track-interaction`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_id: productId,
                    interaction_type: interactionType,
                    duration_ms: durationMs,
                    page_url: window.location.href,
                    session_id: sessionId.current
                })
            });
        } catch (error) {
            console.warn('Failed to track interaction:', error);
        }
    };

    return { trackInteraction, isInitialized };
};

// Individual Product Card with Hover Tracking
const ProductCard = ({ 
    product, 
    onProductClick,
    className = "product-card",
    showHoverCounter = true
}) => {
    const { trackInteraction } = useProductAnalytics();
    const [hoverStartTime, setHoverStartTime] = useState(null);
    const [totalHoverTime, setTotalHoverTime] = useState(0);
    const [hoverCount, setHoverCount] = useState(0);
    const [isVisible, setIsVisible] = useState(false);
    const cardRef = useRef(null);

    // Track when product becomes visible (view tracking)
    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting && !isVisible) {
                    setIsVisible(true);
                    trackInteraction(product.id, 'view');
                }
            },
            { threshold: 0.5 }
        );

        if (cardRef.current) {
            observer.observe(cardRef.current);
        }

        return () => observer.disconnect();
    }, [product.id, trackInteraction, isVisible]);

    const handleMouseEnter = () => {
        const startTime = Date.now();
        setHoverStartTime(startTime);
        setHoverCount(prev => prev + 1);
    };

    const handleMouseLeave = () => {
        if (hoverStartTime) {
            const duration = Date.now() - hoverStartTime;
            setTotalHoverTime(prev => prev + duration);
            
            // Only track meaningful hovers (>500ms)
            if (duration > 500) {
                trackInteraction(product.id, 'hover', duration);
            }
            
            setHoverStartTime(null);
        }
    };

    const handleClick = () => {
        trackInteraction(product.id, 'click');
        if (onProductClick) {
            onProductClick(product);
        }
    };

    const formatTime = (ms) => {
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    return (
        <div
            ref={cardRef}
            className={`${className} analytics-product-card`}
            data-product-id={product.id}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            onClick={handleClick}
            style={{ 
                position: 'relative',
                cursor: 'pointer',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                padding: '16px',
                margin: '8px',
                backgroundColor: '#fff',
                boxShadow: hoverStartTime ? '0 4px 12px rgba(0,0,0,0.15)' : '0 2px 8px rgba(0,0,0,0.1)',
                transform: hoverStartTime ? 'translateY(-2px)' : 'translateY(0)'
            }}
        >
            {/* Hover Analytics Display */}
            {showHoverCounter && (hoverCount > 0 || totalHoverTime > 0) && (
                <div 
                    className="hover-analytics-badge"
                    style={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        backgroundColor: 'rgba(0, 123, 255, 0.9)',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        fontWeight: 'bold',
                        zIndex: 10,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        minWidth: '60px'
                    }}
                >
                    <div>👁️ {hoverCount}</div>
                    <div>⏱️ {formatTime(totalHoverTime)}</div>
                </div>
            )}

            {/* Product Image */}
            <div className="product-image" style={{ marginBottom: '12px' }}>
                <img 
                    src={product.image_url || '/api/placeholder/200/200'} 
                    alt={product.name}
                    style={{
                        width: '100%',
                        height: '200px',
                        objectFit: 'cover',
                        borderRadius: '4px'
                    }}
                />
            </div>

            {/* Product Info */}
            <div className="product-info">
                <h3 style={{ 
                    margin: '0 0 8px 0', 
                    fontSize: '16px', 
                    fontWeight: '600',
                    color: '#333'
                }}>
                    {product.name}
                </h3>
                
                <p style={{ 
                    margin: '0 0 8px 0', 
                    fontSize: '14px', 
                    color: '#666',
                    lineHeight: '1.4'
                }}>
                    {product.description && product.description.length > 100 
                        ? `${product.description.substring(0, 100)}...` 
                        : product.description}
                </p>
                
                <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginTop: '12px'
                }}>
                    <span style={{ 
                        fontSize: '18px', 
                        fontWeight: 'bold', 
                        color: '#007bff' 
                    }}>
                        {product.price} {product.currency || 'TND'}
                    </span>
                    
                    <span style={{ 
                        fontSize: '12px', 
                        color: product.stock_quantity > 0 ? '#28a745' : '#dc3545',
                        fontWeight: '500'
                    }}>
                        {product.stock_quantity > 0 
                            ? `${product.stock_quantity} in stock` 
                            : 'Out of stock'}
                    </span>
                </div>

                <div style={{ 
                    fontSize: '12px', 
                    color: '#888',
                    marginTop: '4px'
                }}>
                    Category: {product.category}
                </div>
            </div>
        </div>
    );
};

// Main Product Grid Component
const ProductGrid = ({ 
    products = [], 
    onProductClick,
    showHoverCounters = true,
    gridColumns = 'auto',
    className = "products-grid"
}) => {
    const { isInitialized } = useProductAnalytics();

    if (!products || products.length === 0) {
        return (
            <div style={{ 
                textAlign: 'center', 
                padding: '40px', 
                color: '#666' 
            }}>
                <h3>No products available</h3>
                <p>Check back soon for new arrivals!</p>
            </div>
        );
    }

    return (
        <div className={className}>
            {/* Analytics Status Indicator */}
            <div style={{ 
                marginBottom: '16px', 
                padding: '8px 12px', 
                backgroundColor: isInitialized ? '#d4edda' : '#fff3cd',
                border: `1px solid ${isInitialized ? '#c3e6cb' : '#ffeaa7'}`,
                borderRadius: '4px',
                fontSize: '12px',
                color: isInitialized ? '#155724' : '#856404'
            }}>
                📊 Analytics: {isInitialized ? 'Active - Tracking user interactions' : 'Initializing...'}
            </div>

            {/* Product Grid */}
            <div 
                style={{
                    display: 'grid',
                    gridTemplateColumns: gridColumns === 'auto' 
                        ? 'repeat(auto-fill, minmax(280px, 1fr))' 
                        : gridColumns,
                    gap: '16px',
                    padding: '0'
                }}
            >
                {products.map((product) => (
                    <ProductCard
                        key={product.id}
                        product={product}
                        onProductClick={onProductClick}
                        showHoverCounter={showHoverCounters}
                    />
                ))}
            </div>

            {/* Grid Summary */}
            <div style={{ 
                marginTop: '20px', 
                textAlign: 'center', 
                color: '#666',
                fontSize: '14px'
            }}>
                Showing {products.length} products
                {showHoverCounters && (
                    <span style={{ marginLeft: '8px' }}>
                        • Hover over products to see engagement metrics
                    </span>
                )}
            </div>
        </div>
    );
};

// Example usage component
const ProductCatalog = () => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);

    // Fetch products from your API
    useEffect(() => {
        const fetchProducts = async () => {
            try {
                const response = await fetch('http://localhost:8000/products');
                const data = await response.json();
                setProducts(data.products || []);
            } catch (error) {
                console.error('Failed to fetch products:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchProducts();
    }, []);

    const handleProductClick = (product) => {
        console.log('Product clicked:', product);
        // Handle product click (e.g., navigate to product detail page)
    };

    if (loading) {
        return (
            <div style={{ 
                textAlign: 'center', 
                padding: '40px' 
            }}>
                Loading products...
            </div>
        );
    }

    return (
        <div style={{ 
            maxWidth: '1200px', 
            margin: '0 auto', 
            padding: '20px' 
        }}>
            <h1 style={{ 
                textAlign: 'center', 
                marginBottom: '30px',
                color: '#333'
            }}>
                CLOESS Product Catalog
            </h1>
            
            <ProductGrid
                products={products}
                onProductClick={handleProductClick}
                showHoverCounters={true}
                gridColumns="repeat(auto-fill, minmax(300px, 1fr))"
            />
        </div>
    );
};

export default ProductCatalog;
export { ProductGrid, ProductCard, useProductAnalytics };

/*
Usage Instructions:

1. Basic Usage:
```jsx
import ProductCatalog from './ProductCatalog';

function App() {
    return <ProductCatalog />;
}
```

2. Custom Grid:
```jsx
import { ProductGrid } from './ProductCatalog';

function MyProductPage({ products }) {
    return (
        <ProductGrid
            products={products}
            showHoverCounters={true}
            gridColumns="repeat(3, 1fr)"
            onProductClick={(product) => {
                window.location.href = `/product/${product.id}`;
            }}
        />
    );
}
```

3. Individual Product Card:
```jsx
import { ProductCard } from './ProductCatalog';

function FeaturedProduct({ product }) {
    return (
        <ProductCard
            product={product}
            showHoverCounter={true}
            onProductClick={(product) => console.log(product)}
        />
    );
}
```

Features:
- 👁️ Hover counter shows number of times hovered
- ⏱️ Total hover time display
- 📊 Real-time analytics tracking
- 🎯 Automatic view tracking when products appear
- 📱 Responsive grid layout
- 🎨 Smooth hover animations
- 📈 Analytics status indicator
*/
