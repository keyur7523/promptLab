#!/bin/bash

# AI Chat Platform - Quick Setup Script
# Run this script to set up the project for first-time use

set -e  # Exit on error

echo "=================================="
echo "AI Chat Platform - Setup"
echo "=================================="
echo ""

# Check for required commands
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is not installed. Please install Docker first."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is not installed. Please install Docker Compose first."; exit 1; }

echo "✓ Docker and Docker Compose are installed"
echo ""

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY environment variable is not set"
    echo ""
    read -p "Enter your OpenAI API key: " OPENAI_KEY
    export OPENAI_API_KEY=$OPENAI_KEY
fi

echo "✓ OpenAI API key is set"
echo ""

# Create .env files from examples
echo "Creating .env files..."

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    # Update OPENAI_API_KEY in backend/.env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-openai-api-key-here/$OPENAI_API_KEY/" backend/.env
    else
        # Linux
        sed -i "s/your-openai-api-key-here/$OPENAI_API_KEY/" backend/.env
    fi
    echo "✓ Created backend/.env"
fi

if [ ! -f frontend/.env ]; then
    cp frontend/.env.example frontend/.env
    echo "✓ Created frontend/.env"
fi

echo ""
echo "Starting Docker services..."
docker-compose up -d postgres redis

echo ""
echo "Waiting for PostgreSQL to be ready..."
sleep 5

echo ""
echo "Initializing database..."
docker-compose run --rm backend python init_db.py

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "To start the application:"
echo "  docker-compose up"
echo ""
echo "Then visit:"
echo "  Frontend: http://localhost:5173"
echo "  Backend API docs: http://localhost:8000/docs"
echo ""
echo "Test API key: test-api-key-12345"
echo "=================================="
