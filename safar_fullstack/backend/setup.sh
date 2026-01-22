#!/bin/bash

echo "🚀 Starting Safar Samarkand Backend Setup..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if MongoDB is installed
if ! command -v mongod &> /dev/null; then
    echo "⚠️  MongoDB is not installed locally."
    echo "You can:"
    echo "1. Install MongoDB: https://www.mongodb.com/docs/manual/installation/"
    echo "2. Use MongoDB Atlas (cloud): https://www.mongodb.com/cloud/atlas"
fi

echo "📦 Installing dependencies..."
npm install

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created. Please update it with your settings."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your MongoDB URI"
echo "2. Start MongoDB: brew services start mongodb-community (macOS)"
echo "3. Seed database: npm run seed"
echo "4. Start server: npm run dev"
echo ""
echo "Server will run at: http://localhost:3000"
