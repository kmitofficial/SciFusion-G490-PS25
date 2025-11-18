# InternAgent Server - Folder Structure

```
InternAgent/
├── server/                          # New server application
│   ├── app/                        # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration settings
│   │   ├── dependencies.py         # Dependency injection
│   │   └── middleware.py           # Custom middleware
│   │
│   ├── api/                        # API routes and endpoints
│   │   ├── __init__.py
│   │   ├── v1/                     # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/          # Endpoint modules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── experiments.py  # Experiment CRUD operations
│   │   │   │   ├── papers.py       # Paper search and retrieval
│   │   │   │   ├── models.py       # LLM model management
│   │   │   │   ├── auth.py         # Authentication endpoints
│   │   │   │   ├── websockets.py   # WebSocket endpoints
│   │   │   │   └── health.py       # Health check endpoints
│   │   │   └── api.py              # API router aggregator
│   │   └── deps.py                 # API dependencies
│   │
│   ├── core/                       # Core business logic
│   │   ├── __init__.py
│   │   ├── auth.py                 # Authentication logic
│   │   ├── security.py             # Security utilities
│   │   ├── experiment_manager.py   # Experiment orchestration
│   │   ├── paper_service.py        # Paper search service
│   │   ├── model_service.py        # LLM model service
│   │   └── websocket_manager.py    # WebSocket connection management
│   │
│   ├── models/                     # Database models
│   │   ├── __init__.py
│   │   ├── database.py             # Database connection
│   │   ├── user.py                 # User model
│   │   ├── experiment.py           # Experiment model
│   │   ├── paper.py                # Paper model
│   │   └── result.py               # Result model
│   │
│   ├── schemas/                    # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py                 # User schemas
│   │   ├── experiment.py           # Experiment schemas
│   │   ├── paper.py                # Paper schemas
│   │   ├── result.py               # Result schemas
│   │   └── common.py               # Common schemas
│   │
│   ├── services/                   # External service integrations
│   │   ├── __init__.py
│   │   ├── ollama_service.py       # Ollama integration
│   │   ├── arxiv_service.py        # arXiv API service
│   │   ├── file_service.py         # File management
│   │   └── notification_service.py # Notifications
│   │
│   ├── utils/                      # Utility functions
│   │   ├── __init__.py
│   │   ├── logging.py              # Logging configuration
│   │   ├── validation.py           # Data validation
│   │   ├── formatting.py           # Data formatting
│   │   └── helpers.py              # General helpers
│   │
│   ├── static/                     # Static files (optional)
│   │   ├── docs/                   # API documentation assets
│   │   └── uploads/                # File uploads
│   │
│   ├── tests/                      # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py             # Test configuration
│   │   ├── test_api/               # API tests
│   │   ├── test_core/              # Core logic tests
│   │   └── test_services/          # Service tests
│   │
│   ├── requirements.txt            # Server dependencies
│   ├── Dockerfile                 # Docker configuration
│   ├── docker-compose.yml         # Multi-service setup
│   └── README.md                  # Server documentation
│
├── frontend/                       # Frontend application (optional)
│   ├── public/                     # Public assets
│   ├── src/                        # Source code
│   │   ├── components/             # React/Vue components
│   │   ├── services/               # API client services
│   │   ├── stores/                 # State management
│   │   └── utils/                  # Frontend utilities
│   ├── package.json
│   └── README.md
│
├── docker/                         # Docker configurations
│   ├── server.Dockerfile
│   ├── frontend.Dockerfile
│   └── nginx.conf
│
├── scripts/                        # Deployment and utility scripts
│   ├── setup_server.sh
│   ├── deploy.sh
│   └── migrate_db.py
│
└── docs/                          # Enhanced documentation
    ├── api_documentation.md        # API reference
    ├── server_setup.md             # Server setup guide
    └── deployment_guide.md         # Deployment instructions
```

## 🔧 **Technology Stack**

### Backend
- **Framework**: FastAPI (high performance, auto-documentation)
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Authentication**: JWT tokens with OAuth2
- **Real-time**: WebSockets for live updates
- **Caching**: Redis for performance
- **Task Queue**: Celery for background processing

### Frontend (Recommended)
- **Framework**: React.js or Vue.js
- **State Management**: Redux/Zustand or Pinia
- **UI Library**: Material-UI or Tailwind CSS
- **Real-time**: WebSocket client
- **HTTP Client**: Axios or Fetch API

### DevOps
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx
- **Process Management**: Supervisor or PM2
- **Monitoring**: Prometheus + Grafana (optional)

## 📡 **API Endpoints Design**

### Core Endpoints
```
GET    /api/v1/health              # Health check
POST   /api/v1/auth/login          # User authentication
POST   /api/v1/auth/logout         # User logout
GET    /api/v1/auth/me             # Current user info

# Experiments
GET    /api/v1/experiments         # List experiments
POST   /api/v1/experiments         # Create experiment
GET    /api/v1/experiments/{id}    # Get experiment details
PUT    /api/v1/experiments/{id}    # Update experiment
DELETE /api/v1/experiments/{id}    # Delete experiment
POST   /api/v1/experiments/{id}/start  # Start experiment
POST   /api/v1/experiments/{id}/stop   # Stop experiment

# Papers
GET    /api/v1/papers/search       # Search papers
GET    /api/v1/papers/{id}         # Get paper details
POST   /api/v1/papers/batch        # Get multiple papers

# Models
GET    /api/v1/models              # List available models
GET    /api/v1/models/{id}/status  # Model status

# Results
GET    /api/v1/results/{exp_id}    # Get experiment results
GET    /api/v1/results/{exp_id}/download  # Download results

# WebSocket
WS     /api/v1/ws/experiments/{id} # Real-time experiment updates
```