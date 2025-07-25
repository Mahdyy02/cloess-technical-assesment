import React, { useRef, useEffect, useCallback } from 'react';

/**
 * Invisible Product Analytics Tracker
 * Tracks user interactions without showing any UI
 */

const ProductHoverTracker = ({ 
    product, 
    children, 
    apiBaseUrl = 'http://localhost:8000'
}) => {
    const trackerRef = useRef(null);
    const hoverStartTime = useRef(null);
    const hasViewed = useRef(false);

    const trackInteraction = useCallback(async (type, duration = null) => {
        try {
            await fetch(`${apiBaseUrl}/analytics/track-interaction`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_id: product.id,
                    interaction_type: type,
                    duration_ms: duration,
                    page_url: window.location.href
                })
            });
        } catch (error) {
            // Silent fail - analytics shouldn't break the app
        }
    }, [apiBaseUrl, product.id]);

    // Initialize session on mount
    useEffect(() => {
        const initSession = async () => {
            try {
                await fetch(`${apiBaseUrl}/analytics/session`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
            } catch (error) {
                // Silent fail - analytics shouldn't break the app
            }
        };
        initSession();
    }, [apiBaseUrl]);

    // Track product view when it becomes visible
    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting && !hasViewed.current) {
                    hasViewed.current = true;
                    trackInteraction('view');
                }
            },
            { threshold: 0.5 }
        );

        if (trackerRef.current) {
            observer.observe(trackerRef.current);
        }

        return () => observer.disconnect();
    }, [trackInteraction]);

    const handleMouseEnter = () => {
        hoverStartTime.current = Date.now();
    };

    const handleMouseLeave = () => {
        if (hoverStartTime.current) {
            const duration = Date.now() - hoverStartTime.current;
            if (duration > 100) { // Track any meaningful hover
                trackInteraction('hover', duration);
            }
            hoverStartTime.current = null;
        }
    };

    const handleClick = () => {
        trackInteraction('click');
    };

    return (
        <div
            ref={trackerRef}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            onClick={handleClick}
            style={{ display: 'contents' }} // Invisible wrapper
            data-product-id={product.id}
        >
            {children}
        </div>
    );
};

export default ProductHoverTracker;
