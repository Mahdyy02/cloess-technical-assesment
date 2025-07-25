import React, { useEffect, useRef, useState } from 'react';

/**
 * CLOESS Analytics Hook for React
 * Provides easy analytics tracking for React components
 */
export const useCLOESSAnalytics = (apiBaseUrl = 'http://localhost:8000') => {
    const [analytics, setAnalytics] = useState(null);
    const [isInitialized, setIsInitialized] = useState(false);
    
    useEffect(() => {
        const initAnalytics = async () => {
            try {
                const analyticsInstance = new CLOESSAnalytics(apiBaseUrl);
                await analyticsInstance.initializeSession();
                setAnalytics(analyticsInstance);
                setIsInitialized(true);
            } catch (error) {
                console.warn('Failed to initialize analytics:', error);
            }
        };
        
        initAnalytics();
    }, [apiBaseUrl]);
    
    const trackProductHover = (productId, duration) => {
        if (analytics && isInitialized) {
            analytics.trackInteraction(productId, 'hover', duration);
        }
    };
    
    const trackProductClick = (productId) => {
        if (analytics && isInitialized) {
            analytics.trackProductClick(productId);
        }
    };
    
    const trackProductView = (productId) => {
        if (analytics && isInitialized) {
            analytics.trackProductView(productId);
        }
    };
    
    return {
        isInitialized,
        trackProductHover,
        trackProductClick,
        trackProductView
    };
};

/**
 * ProductCard component with built-in analytics tracking
 */
export const AnalyticsProductCard = ({ 
    product, 
    children, 
    className = '',
    onProductClick,
    ...props 
}) => {
    const { trackProductHover, trackProductClick, trackProductView } = useCLOESSAnalytics();
    const [hoverStartTime, setHoverStartTime] = useState(null);
    const cardRef = useRef(null);
    
    // Track product view using Intersection Observer
    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    trackProductView(product.id);
                }
            },
            { threshold: 0.5 }
        );
        
        if (cardRef.current) {
            observer.observe(cardRef.current);
        }
        
        return () => observer.disconnect();
    }, [product.id, trackProductView]);
    
    const handleMouseEnter = () => {
        setHoverStartTime(Date.now());
    };
    
    const handleMouseLeave = () => {
        if (hoverStartTime) {
            const duration = Date.now() - hoverStartTime;
            if (duration > 500) { // Only track meaningful hovers
                trackProductHover(product.id, duration);
            }
            setHoverStartTime(null);
        }
    };
    
    const handleClick = () => {
        trackProductClick(product.id);
        if (onProductClick) {
            onProductClick(product);
        }
    };
    
    return (
        <div
            ref={cardRef}
            className={`analytics-product-card ${className}`}
            data-product-id={product.id}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            onClick={handleClick}
            {...props}
        >
            {children}
        </div>
    );
};

/**
 * Higher-order component for adding analytics to existing product components
 */
export const withProductAnalytics = (WrappedComponent) => {
    return function AnalyticsWrappedComponent({ product, ...props }) {
        const { trackProductHover, trackProductClick, trackProductView } = useCLOESSAnalytics();
        const [hoverStartTime, setHoverStartTime] = useState(null);
        const componentRef = useRef(null);
        
        // Track product view
        useEffect(() => {
            const observer = new IntersectionObserver(
                ([entry]) => {
                    if (entry.isIntersecting) {
                        trackProductView(product.id);
                    }
                },
                { threshold: 0.5 }
            );
            
            if (componentRef.current) {
                observer.observe(componentRef.current);
            }
            
            return () => observer.disconnect();
        }, [product.id, trackProductView]);
        
        const handleMouseEnter = () => {
            setHoverStartTime(Date.now());
        };
        
        const handleMouseLeave = () => {
            if (hoverStartTime) {
                const duration = Date.now() - hoverStartTime;
                if (duration > 500) {
                    trackProductHover(product.id, duration);
                }
                setHoverStartTime(null);
            }
        };
        
        const handleClick = () => {
            trackProductClick(product.id);
        };
        
        return (
            <div
                ref={componentRef}
                data-product-id={product.id}
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
                onClick={handleClick}
            >
                <WrappedComponent product={product} {...props} />
            </div>
        );
    };
};

/**
 * Analytics class for non-React usage (same as vanilla JS version)
 */
class CLOESSAnalytics {
    constructor(apiBaseUrl = 'http://localhost:8000') {
        this.apiBaseUrl = apiBaseUrl;
        this.sessionId = this.generateSessionId();
        this.hoverTimers = new Map();
        this.isInitialized = false;
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    async initializeSession() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/analytics/session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Analytics session initialized:', data);
                this.isInitialized = true;
                return true;
            }
        } catch (error) {
            console.warn('Failed to initialize analytics session:', error);
            return false;
        }
    }
    
    async trackInteraction(productId, interactionType, durationMs = null) {
        if (!this.isInitialized) {
            return;
        }
        
        try {
            const payload = {
                product_id: productId,
                interaction_type: interactionType,
                duration_ms: durationMs,
                page_url: window.location.href,
                session_id: this.sessionId
            };
            
            await fetch(`${this.apiBaseUrl}/analytics/track-interaction`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
        } catch (error) {
            console.warn('Failed to track interaction:', error);
        }
    }
    
    trackProductClick(productId) {
        this.trackInteraction(productId, 'click');
    }
    
    trackProductView(productId) {
        this.trackInteraction(productId, 'view');
    }
}

export default CLOESSAnalytics;

/*
Usage Examples:

1. Using the hook:
```jsx
function ProductGrid() {
    const { trackProductClick, isInitialized } = useCLOESSAnalytics();
    
    return (
        <div className="product-grid">
            {products.map(product => (
                <div key={product.id} onClick={() => trackProductClick(product.id)}>
                    {product.name}
                </div>
            ))}
        </div>
    );
}
```

2. Using the AnalyticsProductCard component:
```jsx
function ProductList() {
    return (
        <div>
            {products.map(product => (
                <AnalyticsProductCard 
                    key={product.id}
                    product={product}
                    className="product-card"
                >
                    <img src={product.image} alt={product.name} />
                    <h3>{product.name}</h3>
                    <p>${product.price}</p>
                </AnalyticsProductCard>
            ))}
        </div>
    );
}
```

3. Using the HOC:
```jsx
const AnalyticsProductCard = withProductAnalytics(ProductCard);

function App() {
    return (
        <div>
            {products.map(product => (
                <AnalyticsProductCard key={product.id} product={product} />
            ))}
        </div>
    );
}
```
*/
