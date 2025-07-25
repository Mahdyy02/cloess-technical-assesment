@echo off
REM CLOESS Quick Setup Script for Windows
REM This script automates the setup process for the CLOESS platform

echo 🛍️ CLOESS Setup Script
echo ======================

REM Check if we're in the right directory
if not exist "README.md" (
    echo ❌ Error: Please run this script from the CLOESS project root directory
    exit /b 1
)
if not exist "backend" (
    echo ❌ Error: Backend directory not found
    exit /b 1
)
if not exist "front" (
    echo ❌ Error: Frontend directory not found
    exit /b 1
)

echo 📋 Starting CLOESS setup...

REM Backend setup
echo 🐍 Setting up backend...
cd backend

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating Python virtual environment...
python -m venv venv

REM Activate virtual environment
echo ⚡ Activating virtual environment...
call venv\Scripts\activate.bat

REM Install Python dependencies
echo 📥 Installing Python dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo ⚙️ Creating .env file...
    (
        echo # Database configuration
        echo DB_USER=postgres
        echo DB_PASSWORD=your_postgres_password_here
        echo DB_NAME=cloess
        echo DB_HOST=localhost
        echo DB_PORT=5432
        echo.
        echo # OpenRouter API key for chatbot ^(get from https://openrouter.ai^)
        echo OPENROUTER_API_KEY=sk-your-api-key-here
    ) > .env
    echo 📝 Please edit backend\.env file with your actual database credentials
)

cd ..

REM Frontend setup
echo ⚛️ Setting up frontend...
cd front

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    exit /b 1
)

REM Install Node.js dependencies
echo 📥 Installing Node.js dependencies...
npm install

cd ..

echo.
echo ✅ Setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Install PostgreSQL if not already installed
echo 2. Create the 'cloess' database: CREATE DATABASE cloess;
echo 3. Run the SQL script: psql -U postgres -d cloess -f database_complete_setup.sql
echo 4. Edit backend\.env with your database credentials
echo 5. Start the backend: cd backend ^&^& python main.py
echo 6. Start the frontend: cd front ^&^& npm start
echo.
echo 🎉 Your CLOESS platform will be ready!

pause
