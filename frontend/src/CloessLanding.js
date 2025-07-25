import React, { useEffect, useState, useRef } from 'react';
import SellerBotPopup from './SellerBotPopup';
import ProductHoverTracker from './ProductHoverTracker';
import './CloessLanding.css';

const MAX_SCALE = 1;
const MIN_SCALE = 0.4;

function CloessLanding() {
  const [showSticky, setShowSticky] = useState(false);
  const [scale, setScale] = useState(MAX_SCALE);
  const [showSellerBot, setShowSellerBot] = useState(false);
  const [gifLoaded, setGifLoaded] = useState(false);
  const [showChatbot, setShowChatbot] = useState(false);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const gridRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      const heroHeight = window.innerHeight;
      const scrollY = window.scrollY;
      if (scrollY < heroHeight) {
        const progress = scrollY / heroHeight;
        const newScale = MAX_SCALE - (MAX_SCALE - MIN_SCALE) * progress;
        setScale(newScale);
        setShowSticky(false);
      } else {
        setScale(MIN_SCALE);
        setShowSticky(true);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const observer = new window.IntersectionObserver(
      ([entry]) => setShowSellerBot(entry.isIntersecting),
      { threshold: 0.2 }
    );
    if (gridRef.current) observer.observe(gridRef.current);
    return () => observer.disconnect();
  }, []);

  // Show chatbot only after gif is loaded and user has scrolled to products
  useEffect(() => {
    if (gifLoaded && showSellerBot) {
      const timer = setTimeout(() => {
        setShowChatbot(true);
      }, 2000); // Wait 2 seconds after reaching products section
      return () => clearTimeout(timer);
    }
  }, [gifLoaded, showSellerBot]);

  const handleGifLoad = () => {
    setGifLoaded(true);
  };

  const closeChatbot = () => {
    setShowChatbot(false);
  };

  // Fetch products from API
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8000/products?limit=6');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setProducts(data.products || []);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch products:', err);
        setError('Failed to load products. Please try again later.');
        // Fallback to static products if API fails
        setProducts([
          { id: 1, name: 'Carthagean Robe', price: 120, currency: 'TND', image_url: 'https://www.needleme.fr/sites/default/files/upload/professional-pattern/pictures/1887c690a14.jpg' },
          { id: 2, name: 'Artisan Shawl', price: 80, currency: 'TND', image_url: 'https://m.media-amazon.com/images/I/71sZqZLR0RL._UY350_.jpg' },
          { id: 3, name: 'Handmade Bag', price: 95, currency: 'TND', image_url: 'https://www.zwende.com/cdn/shop/files/RebornTreasuresTheUpcycledPatchworkJholaBag_2.jpg?v=1695648507&width=1080' },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  return (
    <div className="cloess-landing-root">
      <div className="cloess-hero-section">
        <img
          src={require('./intro.gif')}
          alt="Intro animation"
          className="cloess-hero-gif"
          onLoad={handleGifLoad}
        />
        <div
          className="cloess-hero-logo"
          style={{
            transform: `translate(-50%, -50%) scale(${scale})`
          }}
        >
          CLOESS
        </div>
      </div>
      <div className={`cloess-sticky-logo${showSticky ? ' visible' : ''}`}>CLOESS</div>
      <div className="cloess-product-grid-section" ref={gridRef}>
        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}
        {loading ? (
          <div className="loading-spinner">
            <p>Loading beautiful Tunisian products...</p>
          </div>
        ) : (
          <div className="cloess-product-grid">
            {products.map((product) => (
              <ProductHoverTracker 
                key={product.id} 
                product={product}
                apiBaseUrl="http://localhost:8000"
              >
                <div className="cloess-product-card">
                  <img 
                    src={product.image_url || product.img} 
                    alt={product.name}
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/300x300?text=Image+Not+Available';
                    }}
                  />
                  <h3>{product.name}</h3>
                  <p>{product.price} {product.currency || 'TND'}</p>
                  {product.description && (
                    <p className="product-description">{product.description}</p>
                  )}
                  <button>Buy</button>
                </div>
              </ProductHoverTracker>
            ))}
          </div>
        )}
      </div>
      <SellerBotPopup show={showChatbot} onClose={closeChatbot} />
    </div>
  );
}

export default CloessLanding; 