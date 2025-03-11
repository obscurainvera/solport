# SOL PORT

<div align="center">
  <img src="frontend/solport/src/logo.svg" alt="SOL PORT Logo" width="100" height="100">
</div>

SOL PORT is a comprehensive Solana portfolio tracking and analytics platform that helps users monitor smart money wallets, analyze investment strategies, and track portfolio performance.

## 🚀 Features

- **Portfolio Summary**: Track and analyze your Solana portfolio performance
- **Smart Money Tracking**: Follow and analyze top-performing Solana wallets
- **Strategy Builder**: Create and backtest custom investment strategies
- **Operations Dashboard**: Monitor system health and performance
- **Analytics Framework**: Deep insights into market trends and wallet behaviors

## 🏗️ Architecture

### Backend

The backend is built with Flask and provides a RESTful API for the frontend. It includes:

- **Flask API Server**: Handles HTTP requests and serves data to the frontend
- **Scheduler**: Manages recurring jobs using APScheduler
- **Database Layer**: SQLite and DuckDB for data storage and retrieval
- **Analytics Framework**: Processes and analyzes blockchain data

### Frontend

The frontend is built with React and communicates with the backend API:

- **React SPA**: Modern, responsive user interface
- **Bootstrap**: For styling and responsive design
- **React Router**: For navigation between different sections
- **React Icons**: For UI components

## 🛠️ Tech Stack

### Backend
- Python
- Flask
- SQLAlchemy
- APScheduler
- Flask-CORS

### Frontend
- React
- React Router
- Bootstrap
- React Icons

## 📋 Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn

## 🔧 Setup & Installation

### Backend Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/sol-port.git
   cd sol-port
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database
   ```bash
   python app.py init
   ```

5. Start the backend server
   ```bash
   python app.py
   ```

### Frontend Setup

1. Navigate to the frontend directory
   ```bash
   cd frontend/solport
   ```

2. Install dependencies
   ```bash
   npm install
   # or with yarn
   yarn install
   ```

3. Start the development server
   ```bash
   npm start
   # or with yarn
   yarn start
   ```

## 🔍 Usage

1. Open your browser and navigate to `http://localhost:3000` to access the frontend
2. The backend API is available at `http://localhost:8080`
3. Use the navigation menu to explore different sections of the application

## 🧪 Testing

### Backend Tests
```bash
# In the root directory
python -m unittest discover
```

### Frontend Tests
```bash
# In the frontend/solport directory
npm test
# or with yarn
yarn test
```

## 📁 Project Structure

```
sol-port/
├── api/                    # API endpoints
├── database/               # Database models and handlers
├── framework/              # Core framework components
├── scheduler/              # Job scheduling system
├── services/               # Business logic services
├── parsers/                # Data parsers
├── logs/                   # Application logs
├── examples/               # Example code and documentation
├── frontend/               # Frontend React application
│   └── solport/
│       ├── public/         # Static assets
│       └── src/            # React source code
│           ├── components/ # React components
│           └── ...         # Other frontend files
├── app.py                  # Main application entry point
├── orchestrator.py         # Service orchestrator
└── requirements.txt        # Python dependencies
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Solana Foundation
- All contributors who have helped shape this project 