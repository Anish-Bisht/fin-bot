#!/bin/bash

# FinBot - Complete Application Setup & Run Guide

echo "🤖 FinBot - AI Equity Research Assistant"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this from the project root (fin-chatbot directory)"
    exit 1
fi

echo "📋 Pre-flight Checks:"
echo "✓ Project structure verified"
echo ""

# Backend setup
echo "🔧 Backend Setup (Python/FastAPI)"
echo "-----------------------------------"
echo "1. Creating .data directory for SQLite database..."
mkdir -p .data
echo "   ✓ .data directory ready"
echo ""

echo "2. Backend should be running on: http://localhost:8000"
echo "   Start backend with: ./.venv/bin/python run.py"
echo ""

# Frontend setup
echo "🎨 Frontend Setup (Next.js)"
echo "----------------------------"
cd ui

if [ ! -d "node_modules" ]; then
    echo "1. Installing dependencies..."
    npm install
    echo "   ✓ Dependencies installed"
else
    echo "1. ✓ Dependencies already installed"
fi

if [ ! -f ".env.local" ]; then
    echo ""
    echo "2. Creating .env.local..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
    echo "   ✓ Environment configured"
fi

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📝 To run the application:"
echo "============================"
echo ""
echo "Terminal 1 - Start Backend:"
echo "  cd /Users/anishbisht/project/Code\\ Basic/fin-chatbot"
echo "  uv run uvicorn app.main:app --port 8000"
echo ""
echo "Terminal 2 - Start Frontend:"
echo "  cd /Users/anishbisht/project/Code\\ Basic/fin-chatbot/ui"
echo "  npm run dev"
echo ""
echo "🌐 Access the application:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "📚 Features:"
echo "  • Login Screen & JWT Authentication"
echo "  • 5 Roles defined with specific departments (Employee, Finance, Engineering, Marketing, c_level)"
echo "  • Admin Dashboard (for c_level) to manage Roles & Documents"
echo "  • Document Indexing with Semantic search based on Role-Based Access Control"
echo "  • Agent respects user permissions"
echo ""
