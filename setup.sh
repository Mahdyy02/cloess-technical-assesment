#!/bin/bash
# CLOESS Quick Setup Script
# This script automates the setup process for the CLOESS platform

echo "🛍️ CLOESS Setup Script"
echo "======================"

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "front" ]; then
    echo "❌ Error: Please run this script from the CLOESS project root directory"
    exit 1
fi

echo "📋 Starting CLOESS setup..."

# Backend setup
echo "🐍 Setting up backend..."
cd backend

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python -m venv venv

# Activate virtual environment
echo "⚡ Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    cat > .env << EOF
# Database configuration
DB_USER=postgres
DB_PASSWORD=your_postgres_password_here
DB_NAME=cloess
DB_HOST=localhost
DB_PORT=5432

# OpenRouter API key for chatbot (get from https://openrouter.ai)
OPENROUTER_API_KEY=sk-your-api-key-here
EOF
    echo "📝 Please edit backend/.env file with your actual database credentials"
fi

cd ..

# Frontend setup
echo "⚛️ Setting up frontend..."
cd front

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Install Node.js dependencies
echo "📥 Installing Node.js dependencies..."
npm install

cd ..

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Install PostgreSQL if not already installed"
echo "2. Create the 'cloess' database: CREATE DATABASE cloess;"
echo "3. Run the SQL script: psql -U postgres -d cloess -f database_complete_setup.sql"
echo "4. Edit backend/.env with your database credentials"
echo "5. Start the backend: cd backend && python main.py"
echo "6. Start the frontend: cd front && npm start"
echo ""
echo "🎉 Your CLOESS platform will be ready!"
