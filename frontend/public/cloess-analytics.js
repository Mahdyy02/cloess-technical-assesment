/**
 * CLOESS Analytics Tracker
 * Tracks user interactions with products for analytics
 */

class CLOESSAnalytics {
    constructor(apiBaseUrl = 'http://localhost:8000') {
        this.apiBaseUrl = apiBaseUrl;
        this.sessionId = this.generateSessionId();
        this.hoverTimers = new Map(); // Track hover start times
        this.isInitialized = false;
        
        // Initialize session tracking
        this.initializeSession();
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
            }
        } catch (error) {
            console.warn('Failed to initialize analytics session:', error);
        }
    }
    
    async trackInteraction(productId, interactionType, durationMs = null) {
        if (!this.isInitialized) {
            console.warn('Analytics not initialized yet');
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
            
            console.log('Tracked interaction:', payload);
        } catch (error) {
            console.warn('Failed to track interaction:', error);
        }
    }
    
    // Track when user hovers over a product
    trackProductHoverStart(productId) {
        const startTime = Date.now();
        this.hoverTimers.set(productId, startTime);
    }
    
    // Track when user stops hovering over a product
    trackProductHoverEnd(productId) {
        const startTime = this.hoverTimers.get(productId);
        if (startTime) {
            const duration = Date.now() - startTime;
            this.hoverTimers.delete(productId);
            
            // Only track if hover was meaningful (more than 500ms)
            if (duration > 500) {
                this.trackInteraction(productId, 'hover', duration);
            }
        }
    }
    
    // Track product clicks
    trackProductClick(productId) {
        this.trackInteraction(productId, 'click');
    }
    
    // Track product views (when product appears in viewport)
    trackProductView(productId) {
        this.trackInteraction(productId, 'view');
    }
    
    // Setup automatic tracking for products with specific classes/attributes
    setupAutoTracking() {
        // Track product hovers
        document.addEventListener('mouseover', (event) => {
            const productElement = event.target.closest('[data-product-id]');
            if (productElement) {
                const productId = parseInt(productElement.dataset.productId);
                this.trackProductHoverStart(productId);
            }
        });
        
        document.addEventListener('mouseout', (event) => {
            const productElement = event.target.closest('[data-product-id]');
            if (productElement) {
                const productId = parseInt(productElement.dataset.productId);
                this.trackProductHoverEnd(productId);
            }
        });
        
        // Track product clicks
        document.addEventListener('click', (event) => {
            const productElement = event.target.closest('[data-product-id]');
            if (productElement) {
                const productId = parseInt(productElement.dataset.productId);
                this.trackProductClick(productId);
            }
        });
        
        // Track product views using Intersection Observer
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && entry.target.dataset.productId) {
                    const productId = parseInt(entry.target.dataset.productId);
                    this.trackProductView(productId);
                }
            });
        }, {
            threshold: 0.5 // Track when 50% of product is visible
        });
        
        // Observe all product elements
        document.querySelectorAll('[data-product-id]').forEach(element => {
            observer.observe(element);
        });
        
        console.log('CLOESS Analytics auto-tracking enabled');
    }
}

// Usage instructions:
/*
1. Include this script in your HTML:
   <script src="cloess-analytics.js"></script>

2. Initialize analytics:
   const analytics = new CLOESSAnalytics();
   analytics.setupAutoTracking();

3. Add data-product-id attributes to your product elements:
   <div class="product-card" data-product-id="123">
     <!-- product content -->
   </div>

4. Or track manually:
   analytics.trackProductClick(123);
   analytics.trackProductView(123);

The system will automatically track:
- Product hovers (duration)
- Product clicks
- Product views (when they appear in viewport)
- User sessions with IP geolocation
*/

// Auto-initialize if not in module environment
if (typeof window !== 'undefined' && !window.CLOESSAnalytics) {
    window.CLOESSAnalytics = CLOESSAnalytics;
    
    // Auto-setup when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.cloessAnalytics = new CLOESSAnalytics();
            window.cloessAnalytics.setupAutoTracking();
        });
    } else {
        window.cloessAnalytics = new CLOESSAnalytics();
        window.cloessAnalytics.setupAutoTracking();
    }
}
