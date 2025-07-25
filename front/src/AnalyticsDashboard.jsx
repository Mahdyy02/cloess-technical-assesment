import React, { useState, useEffect } from 'react';

/**
 * Analytics Dashboard Component
 * View hover analytics data for your products
 */

const AnalyticsDashboard = ({ apiBaseUrl = 'http://localhost:8000' }) => {
    const [analytics, setAnalytics] = useState({
        users: [],
        products: [],
        countries: [],
        totalSessions: 0,
        totalInteractions: 0
    });
    const [loading, setLoading] = useState(true);
    const [selectedTab, setSelectedTab] = useState('products');
    const [timeRange, setTimeRange] = useState('24h');

    useEffect(() => {
        fetchAnalytics();
        // Refresh every 30 seconds
        const interval = setInterval(fetchAnalytics, 30000);
        return () => clearInterval(interval);
    }, [timeRange]);

    const fetchAnalytics = async () => {
        try {
            setLoading(true);
            
            const [usersRes, productsRes, countriesRes] = await Promise.all([
                fetch(`${apiBaseUrl}/analytics/users?hours=${getHours(timeRange)}`),
                fetch(`${apiBaseUrl}/analytics/products?hours=${getHours(timeRange)}`),
                fetch(`${apiBaseUrl}/analytics/countries?hours=${getHours(timeRange)}`)
            ]);

            const [users, products, countries] = await Promise.all([
                usersRes.json(),
                productsRes.json(),
                countriesRes.json()
            ]);

            setAnalytics({
                users: users.users || [],
                products: products.products || [],
                countries: countries.countries || [],
                totalSessions: users.users?.length || 0,
                totalInteractions: products.products?.reduce((sum, p) => sum + (p.total_interactions || 0), 0) || 0
            });
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    const getHours = (range) => {
        switch (range) {
            case '1h': return 1;
            case '24h': return 24;
            case '7d': return 168;
            case '30d': return 720;
            default: return 24;
        }
    };

    const formatDuration = (ms) => {
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
        return `${(ms / 60000).toFixed(1)}m`;
    };

    const TabButton = ({ id, label, active, onClick }) => (
        <button
            onClick={() => onClick(id)}
            style={{
                padding: '8px 16px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: active ? '#007bff' : '#f8f9fa',
                color: active ? 'white' : '#333',
                cursor: 'pointer',
                marginRight: '8px',
                fontSize: '14px',
                fontWeight: active ? 'bold' : 'normal'
            }}
        >
            {label}
        </button>
    );

    const StatCard = ({ title, value, subtitle, color = '#007bff' }) => (
        <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            textAlign: 'center',
            border: `3px solid ${color}20`
        }}>
            <h3 style={{ margin: '0 0 8px 0', color, fontSize: '24px' }}>{value}</h3>
            <p style={{ margin: '0', fontWeight: 'bold', color: '#333' }}>{title}</p>
            {subtitle && <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#666' }}>{subtitle}</p>}
        </div>
    );

    if (loading) {
        return (
            <div style={{ padding: '40px', textAlign: 'center' }}>
                <h2>📊 Loading Analytics...</h2>
            </div>
        );
    }

    return (
        <div style={{ 
            padding: '20px', 
            backgroundColor: '#f5f5f5', 
            minHeight: '100vh',
            fontFamily: 'Arial, sans-serif'
        }}>
            <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
                {/* Header */}
                <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '20px'
                }}>
                    <h1 style={{ margin: 0, color: '#333' }}>🎯 CLOESS Analytics Dashboard</h1>
                    
                    <div>
                        <label style={{ marginRight: '8px', fontWeight: 'bold' }}>Time Range:</label>
                        <select 
                            value={timeRange} 
                            onChange={(e) => setTimeRange(e.target.value)}
                            style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #ccc' }}
                        >
                            <option value="1h">Last Hour</option>
                            <option value="24h">Last 24 Hours</option>
                            <option value="7d">Last 7 Days</option>
                            <option value="30d">Last 30 Days</option>
                        </select>
                    </div>
                </div>

                {/* Summary Stats */}
                <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '16px',
                    marginBottom: '30px'
                }}>
                    <StatCard 
                        title="Total Sessions" 
                        value={analytics.totalSessions}
                        subtitle="Unique visitors"
                        color="#28a745"
                    />
                    <StatCard 
                        title="Total Interactions" 
                        value={analytics.totalInteractions}
                        subtitle="Hovers, clicks, views"
                        color="#007bff"
                    />
                    <StatCard 
                        title="Countries" 
                        value={analytics.countries.length}
                        subtitle="Geographic reach"
                        color="#ffc107"
                    />
                    <StatCard 
                        title="Products Viewed" 
                        value={analytics.products.filter(p => p.total_views > 0).length}
                        subtitle="Out of total products"
                        color="#17a2b8"
                    />
                </div>

                {/* Tabs */}
                <div style={{ marginBottom: '20px' }}>
                    <TabButton id="products" label="📦 Products" active={selectedTab === 'products'} onClick={setSelectedTab} />
                    <TabButton id="users" label="👥 Users" active={selectedTab === 'users'} onClick={setSelectedTab} />
                    <TabButton id="countries" label="🌍 Countries" active={selectedTab === 'countries'} onClick={setSelectedTab} />
                </div>

                {/* Content */}
                <div style={{
                    backgroundColor: 'white',
                    padding: '20px',
                    borderRadius: '8px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                    {selectedTab === 'products' && (
                        <div>
                            <h3>Product Performance</h3>
                            {analytics.products.length === 0 ? (
                                <p>No product interactions yet.</p>
                            ) : (
                                <div style={{ overflow: 'auto' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                        <thead>
                                            <tr style={{ backgroundColor: '#f8f9fa' }}>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Product ID</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Views</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Hovers</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Clicks</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Avg Hover Time</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Total Interactions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {analytics.products
                                                .sort((a, b) => (b.total_interactions || 0) - (a.total_interactions || 0))
                                                .map((product, index) => (
                                                <tr key={product.product_id} style={{ backgroundColor: index % 2 === 0 ? '#f8f9fa' : 'white' }}>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>#{product.product_id}</td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>{product.total_views || 0}</td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>{product.total_hovers || 0}</td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>{product.total_clicks || 0}</td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>
                                                        {product.avg_hover_duration ? formatDuration(product.avg_hover_duration) : 'N/A'}
                                                    </td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6', fontWeight: 'bold' }}>
                                                        {product.total_interactions || 0}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}

                    {selectedTab === 'users' && (
                        <div>
                            <h3>User Sessions</h3>
                            {analytics.users.length === 0 ? (
                                <p>No user sessions recorded yet.</p>
                            ) : (
                                <div style={{ overflow: 'auto' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                        <thead>
                                            <tr style={{ backgroundColor: '#f8f9fa' }}>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>IP Address</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Country</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>City</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Total Interactions</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>First Seen</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Last Seen</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {analytics.users
                                                .sort((a, b) => (b.total_interactions || 0) - (a.total_interactions || 0))
                                                .map((user, index) => (
                                                <tr key={user.ip_address} style={{ backgroundColor: index % 2 === 0 ? '#f8f9fa' : 'white' }}>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>{user.ip_address}</td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>{user.country || 'Unknown'}</td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>{user.city || 'Unknown'}</td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6', fontWeight: 'bold' }}>
                                                        {user.total_interactions || 0}
                                                    </td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>
                                                        {user.first_seen ? new Date(user.first_seen).toLocaleString() : 'N/A'}
                                                    </td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>
                                                        {user.last_seen ? new Date(user.last_seen).toLocaleString() : 'N/A'}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}

                    {selectedTab === 'countries' && (
                        <div>
                            <h3>Geographic Distribution</h3>
                            {analytics.countries.length === 0 ? (
                                <p>No geographic data available yet.</p>
                            ) : (
                                <div style={{ overflow: 'auto' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                        <thead>
                                            <tr style={{ backgroundColor: '#f8f9fa' }}>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Country</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Users</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Total Interactions</th>
                                                <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #dee2e6' }}>Avg Interactions/User</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {analytics.countries
                                                .sort((a, b) => (b.total_interactions || 0) - (a.total_interactions || 0))
                                                .map((country, index) => (
                                                <tr key={country.country} style={{ backgroundColor: index % 2 === 0 ? '#f8f9fa' : 'white' }}>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>{country.country}</td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>{country.user_count || 0}</td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6', fontWeight: 'bold' }}>
                                                        {country.total_interactions || 0}
                                                    </td>
                                                    <td style={{ padding: '12px', border: '1px solid #dee2e6' }}>
                                                        {country.user_count > 0 
                                                            ? ((country.total_interactions || 0) / country.user_count).toFixed(1)
                                                            : '0'
                                                        }
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Refresh Info */}
                <div style={{ 
                    marginTop: '20px', 
                    textAlign: 'center', 
                    color: '#666',
                    fontSize: '14px'
                }}>
                    📊 Dashboard refreshes automatically every 30 seconds • Last updated: {new Date().toLocaleTimeString()}
                </div>
            </div>
        </div>
    );
};

export default AnalyticsDashboard;

/*
Usage:
1. Add to your app as a separate route/page:
```jsx
import AnalyticsDashboard from './AnalyticsDashboard';

function App() {
    return (
        <div>
            <Route path="/analytics" component={AnalyticsDashboard} />
        </div>
    );
}
```

2. Or add as a popup/modal in your existing app:
```jsx
const [showAnalytics, setShowAnalytics] = useState(false);

return (
    <div>
        <button onClick={() => setShowAnalytics(true)}>View Analytics</button>
        {showAnalytics && (
            <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'white', zIndex: 1000 }}>
                <button onClick={() => setShowAnalytics(false)}>Close</button>
                <AnalyticsDashboard />
            </div>
        )}
    </div>
);
```
*/
