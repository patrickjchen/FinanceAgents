#!/bin/bash

# FinanceAgents LlamaIndex Environment Setup Script

echo "Setting up FinanceAgents LlamaIndex environment..."
echo "=============================================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements_new.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p vector_db/llamaindex_storage
mkdir -p ../raw_data

# Create .env file template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env template..."
    cat > .env << EOF
# OpenAI API Key (required)
OPENAI_API_KEY=your_openai_api_key_here

# Reddit API credentials (required for Reddit agent)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Optional: Set log level
LOG_LEVEL=INFO
EOF
    echo "⚠️  Please edit .env file with your API keys before running the application"
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Add PDF documents to ../raw_data/ directory (shared across all frameworks)"
echo "3. Run: python test_implementation.py (to test)"
echo "4. Run: python main.py (to start the server)"