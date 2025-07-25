# 🛍️ CLOESS - Tunisian Fashion E-commerce Platform

A modern e-commerce platform for Tunisian fashion featuring an AI-powered chatbot assistant, invisible analytics tracking, and a responsive React frontend with FastAPI backend.

## 🌟 Features

- **🤖 AI Agent Assistant**: LLM-powered AI Agent for customer support
- **📊 Invisible Analytics**: Real-time user behavior tracking without visible UI counters
- **🛍️ Product Catalog**: Dynamic product browsing with categories and search
- **🌍 Geolocation Tracking**: IP-based user location analytics
- **📱 Responsive Design**: Mobile-friendly React frontend
- **🔍 Advanced Search**: Product search by name, description, and category
- **💰 Price Filtering**: Filter products by price range

## 📋 Prerequisites

Before setting up CLOESS, ensure you have the following installed:

### 1. Node.js and npm
**Windows:**
- Download from: https://nodejs.org/en/download/
- Choose LTS version (recommended)
- Verify installation: `node --version` and `npm --version`

**macOS:**
```bash
# Using Homebrew
brew install node
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Python 3.8+
**Windows:**
- Download from: https://python.org/downloads/
- Make sure to check "Add Python to PATH" during installation
- Verify: `python --version`

**macOS:**
```bash
# Using Homebrew
brew install python
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 3. PostgreSQL Database
**Windows:**
- Download from: https://www.postgresql.org/download/windows/
- Remember the password you set for the `postgres` user

**macOS:**
```bash
# Using Homebrew
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 4. Git (Optional but recommended)
- Download from: https://git-scm.com/downloads

## 🗄️ Database Setup

### 1. Create Database
Connect to PostgreSQL and create the CLOESS database:

```sql
-- Connect as postgres user
CREATE DATABASE cloess;
```

**Using psql:**
```bash
psql -U postgres
CREATE DATABASE cloess;
\q
```

### 2. Create Database Tables
Connect to the `cloess` database and run the complete setup script:

**Using psql command:**
```bash
psql -U postgres -d cloess -f database_complete_setup.sql
```

**Or copy and paste the SQL from `database_complete_setup.sql` into pgAdmin query editor.**

This will create all three required tables:
- `products` - Product catalog with categories, prices, and inventory
- `user_sessions` - User tracking with IP-based geolocation  
- `product_interactions` - Analytics data for user behavior tracking

### 3. Sample Data (Optional)
The `database_complete_setup.sql` script includes sample product data. If you want to add more products later, use this format:

```sql
INSERT INTO products (name, price, description, image_url, category, stock_quantity) VALUES
('Product Name', 99.99, 'Product description', '/images/product.jpg', 'Category', 10);
```

## ⚙️ Backend Setup

### 1. Navigate to Backend Directory
```bash
cd backend
```

### 2. Create Python Virtual Environment (Recommended)
**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Dependencies installed:**
- `fastapi` - Web framework
- `httpx` - HTTP client for API calls
- `uvicorn` - ASGI server
- `psycopg2-binary` - PostgreSQL adapter
- `asyncpg` - Async PostgreSQL driver
- `pydantic` - Data validation
- `python-dotenv` - Environment variables

### 4. Configure Environment Variables
Create a `.env` file in the backend directory:

```bash
# Database configuration
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_NAME=cloess
DB_HOST=localhost
DB_PORT=5432

# OpenRouter API key for chatbot (get from https://openrouter.ai)
OPENROUTER_API_KEY=sk-your-api-key-here
```

**Note:** Replace `your_postgres_password` with your actual PostgreSQL password.

### 5. Start the Backend Server
```bash
python main.py
```

**Alternative using uvicorn:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: http://localhost:8000

## 🎨 Frontend Setup

### 1. Navigate to Frontend Directory
```bash
cd front
```

### 2. Install Node.js Dependencies
```bash
npm install
```

**Dependencies installed:**
- `react` - React library
- `react-dom` - React DOM rendering
- `react-scripts` - Create React App scripts
- `react-markdown` - Markdown rendering
- `@testing-library/*` - Testing utilities
- `web-vitals` - Performance monitoring

### 3. Start the Frontend Development Server
```bash
npm start
```

The frontend will be available at: http://localhost:3000

## 🧪 Testing the Setup

### 1. Test Database Connection
Visit: http://localhost:8000/health

**Expected response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. Test API Endpoints

**Get all products:**
```bash
curl http://localhost:8000/products
```

**Get categories:**
```bash
curl http://localhost:8000/categories
```

**Search products:**
```bash
curl "http://localhost:8000/products/search?q=robe"
```

### 3. Test Full Application
Visit: http://localhost:3000

You should see the CLOESS landing page with product grid.

## 📊 Analytics System

The platform includes an invisible analytics system that tracks:

### User Behavior
- **IP-based tracking** with geolocation (country, city)
- **Session duration** and visit frequency
- **Device/browser information** from user agent

### Product Interactions
- **Hover time** (cumulative per user/product)
- **View tracking** when products appear in viewport
- **Click tracking** for purchase intent analysis

### Data Collection
- **No visible counters** - Analytics are completely invisible to users
- **Cumulative tracking** - Hover times accumulate for each user/product combination
- **Real-time geolocation** - User location detected via IP address

### Viewing Analytics Data

**API Endpoints:**
```bash
# User analytics
GET http://localhost:8000/analytics/users

# Product analytics
GET http://localhost:8000/analytics/products

# Country analytics
GET http://localhost:8000/analytics/countries
```

**Command line script:**
```bash
cd backend
python view_analytics.py
```

## 🔧 Development Scripts

### Backend Commands
```bash
# Start development server
python main.py

# Start with uvicorn (alternative)
uvicorn main:app --reload

# View analytics data
python view_analytics.py

# Check dependencies
pip list
```

### Frontend Commands
```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Check dependencies
npm list
```

## 📱 Project Structure

```
CLOESS/
├── README.md                         # 📖 Complete setup guide
├── database_complete_setup.sql       # 🗄️ Database schema and sample data
├── setup.bat                         # 🪟 Windows automated setup script
├── setup.sh                          # 🐧 Linux/macOS automated setup script
│
├── backend/                          # 🐍 Python FastAPI Backend
│   ├── main.py                      # Main FastAPI application
│   ├── database.py                  # Database operations
│   ├── simple_analytics.py          # Analytics manager
│   ├── chatbot_agent.py             # AI chatbot logic
│   ├── view_analytics.py            # Analytics viewing script
│   ├── requirements.txt             # Python dependencies
│   └── .env                         # Environment variables (create this)
│
└── front/                           # ⚛️ React Frontend
    ├── src/                         # React source files
    │   ├── App.js                   # Main React app
    │   ├── CloessLanding.js         # Landing page
    │   ├── ProductHoverTracker.jsx  # Analytics tracking component
    │   ├── ReactAnalytics.jsx       # React analytics hooks
    │   └── ...                      # Other React components
    │
    ├── public/                      # Static assets
    │   ├── index.html               # HTML template
    │   ├── cloess-analytics.js      # Vanilla JS analytics
    │   └── ...                      # Images and assets
    │
    └── package.json                 # npm dependencies
```

## 🚀 API Reference

### Product Endpoints
- `GET /products` - Get all products (with optional category filter)
- `GET /products/{id}` - Get specific product by ID
- `GET /products/search?q={term}` - Search products
- `GET /products/price-range?min_price={min}&max_price={max}` - Filter by price
- `GET /categories` - Get all product categories
- `GET /products/stats` - Get product statistics

### Analytics Endpoints
- `POST /analytics/track-interaction` - Track user interactions
- `POST /analytics/session` - Track user sessions
- `GET /analytics/users` - Get user analytics
- `GET /analytics/products` - Get product analytics
- `GET /analytics/countries` - Get country analytics

### Chatbot Endpoints
- `POST /chat` - Chat with AI assistant

### System Endpoints
- `GET /health` - Health check

## 🐛 Troubleshooting

### Database Connection Issues
1. **PostgreSQL not running**
   ```bash
   # Windows: Start PostgreSQL service
   # macOS: brew services start postgresql
   # Linux: sudo systemctl start postgresql
   ```

2. **Wrong credentials**
   - Check `.env` file in backend directory
   - Verify PostgreSQL username/password
   - Ensure database `cloess` exists

3. **Port conflicts**
   - PostgreSQL default port: 5432
   - Backend default port: 8000
   - Frontend default port: 3000

### Python Issues
1. **Module not found**
   ```bash
   # Activate virtual environment
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Python version**
   - Requires Python 3.8 or higher
   - Check: `python --version`

### Node.js Issues
1. **npm install fails**
   ```bash
   # Clear npm cache
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Port already in use**
   ```bash
   # Kill process on port 3000
   npx kill-port 3000
   ```

### Analytics Not Working
1. **Check backend logs** for database connection errors
2. **Verify tables exist** in PostgreSQL
3. **Check browser console** for JavaScript errors
4. **Ensure API calls** are reaching `http://localhost:8000`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenRouter** for AI chatbot capabilities
- **FastAPI** for the powerful backend framework
- **React** for the dynamic frontend
- **PostgreSQL** for reliable data storage

---

## 🚀 Quick Start Summary

### Automated Setup (Recommended)
Run the setup script to automate the installation process:

**Windows:**
```cmd
setup.bat
```

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup
1. **Install Prerequisites**: Node.js, Python 3.8+, PostgreSQL
2. **Create Database**: `CREATE DATABASE cloess;`
3. **Run SQL Script**: `psql -U postgres -d cloess -f database_complete_setup.sql`
4. **Backend Setup**: 
   ```bash
   cd backend
   pip install -r requirements.txt
   # Create .env file with database credentials
   python main.py
   ```
5. **Frontend Setup**:
   ```bash
   cd front
   npm install
   npm start
   ```
6. **Visit**: http://localhost:3000 for the app, http://localhost:8000 for API

**Your CLOESS platform is now ready! 🎉** 
