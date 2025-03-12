<<<<<<< HEAD
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
=======
# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
>>>>>>> 47e35f6 (Initial commit for frontend/solport)
