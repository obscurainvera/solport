#!/bin/bash
set -e

echo "🚀 Setting up SolPort development environment..."

# Create virtual environment for backend
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt

# Install frontend dependencies
echo "📦 Installing Node.js dependencies..."
cd ../frontend/solport
npm install

# Create environment files
echo "⚙️  Creating environment files..."
cd ../..

# Create backend .env file
cat > backend/.env <<EOL
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URI=sqlite:///../data/portfolio.db
REDIS_URL=redis://redis:6379/0
EOL

# Create frontend .env file
cat > frontend/solport/.env <<EOL
REACT_APP_API_URL=http://localhost:5000
EOL

# Create data directory
mkdir -p data

# Initialize database
echo "💾 Initializing database..."
cd backend
flask db upgrade

# Build frontend
echo "🔨 Building frontend..."
cd ../frontend/solport
npm run build

echo "✨ Setup complete! 🎉"
echo ""
echo "To start the application, run:"
echo "1. Start the backend: cd backend && flask run"
echo "2. Start the frontend: cd frontend/solport && npm start"
echo ""
echo "Or use Docker Compose: docker-compose up --build"

