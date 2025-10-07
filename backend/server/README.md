# InternAgent Server Setup Guide

This guide explains how to set up and run the InternAgent web server to provide API access to the research automation system.

## 🚀 Quick Start

### 1. Install Server Dependencies

```bash
cd server
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the server directory:

```env
# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=true

# Security
SECRET_KEY=your-secret-key-change-in-production-12345

# Database (SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite:///./internagent.db

# Redis (for caching and WebSocket management)
REDIS_URL=redis://localhost:6379

# CORS Settings
ALLOWED_HOSTS=["http://localhost:3000","http://localhost:8080","http://localhost:5173"]

# File Storage
UPLOAD_DIR=./uploads
RESULTS_DIR=./results

# InternAgent Configuration
DEFAULT_MODEL=localhost-deepseek-v2-16b
DEFAULT_CODE_MODEL=localhost-deepseek-v2-16b

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# External API Keys (optional)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
DEEPSEEK_API_KEY=your-deepseek-key
```

### 3. Start Required Services

**Start Ollama (if using local models):**
```bash
ollama serve
```

**Start Redis (optional, for advanced features):**
```bash
# Windows (if you have Redis installed)
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

### 4. Run the Server

```bash
# From the server directory
python app/main.py

# Or using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📡 API Usage Examples

### Paper Search

```bash
# Search for papers
curl -X GET "http://localhost:8000/api/v1/papers/search?query=transformer%20attention&max_results=5"

# Get paper details
curl -X GET "http://localhost:8000/api/v1/papers/2106.04554"
```

### Experiment Management

```bash
# Create a new experiment
curl -X POST "http://localhost:8000/api/v1/experiments/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Classification Experiment",
    "experiment_type": "point_classification_modelnet",
    "model": "localhost-deepseek-v2-16b",
    "num_ideas": 5,
    "use_rag": true,
    "topic": "point cloud deep learning"
  }'

# Start an experiment
curl -X POST "http://localhost:8000/api/v1/experiments/{experiment_id}/start"

# Get experiment status
curl -X GET "http://localhost:8000/api/v1/experiments/{experiment_id}/status"
```

### Model Management

```bash
# List available models
curl -X GET "http://localhost:8000/api/v1/models/"

# Check model status
curl -X GET "http://localhost:8000/api/v1/models/localhost-deepseek-v2-16b/status"
```

## 🔌 WebSocket Integration

### Real-time Experiment Updates

```javascript
// JavaScript WebSocket client example
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/experiments/{experiment_id}');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Experiment update:', data);
    
    // Handle different update types
    if (data.type === 'status_update') {
        updateProgressBar(data.data.progress);
        updateStatus(data.data.status);
    }
};

ws.onopen = function(event) {
    console.log('Connected to experiment updates');
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

### Global System Updates

```javascript
// Monitor system-wide updates
const globalWs = new WebSocket('ws://localhost:8000/api/v1/ws/global');

globalWs.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'system_status') {
        updateSystemMetrics(data.data);
    }
};
```

## 🏗️ Architecture Overview

### Server Structure

```
server/
├── app/                    # FastAPI application setup
│   ├── main.py            # Application entry point
│   └── config.py          # Configuration management
│
├── api/v1/endpoints/      # REST API endpoints
│   ├── experiments.py     # Experiment management
│   ├── papers.py          # Paper search & retrieval
│   ├── models.py          # Model management
│   ├── auth.py            # Authentication
│   ├── websockets.py      # WebSocket endpoints
│   └── health.py          # Health checks
│
├── core/                  # Business logic
│   ├── experiment_manager.py  # Experiment orchestration
│   └── websocket_manager.py   # WebSocket management
│
├── schemas/               # Pydantic data models
│   ├── experiment.py      # Experiment schemas
│   └── paper.py           # Paper schemas
│
└── services/              # External integrations
    ├── arxiv_service.py   # arXiv API integration
    └── file_service.py    # File operations
```

### Key Features

1. **RESTful API**: Complete CRUD operations for experiments and papers
2. **Real-time Updates**: WebSocket support for live experiment monitoring
3. **arXiv Integration**: Direct integration with arXiv for paper search
4. **Model Management**: Support for local (Ollama) and cloud LLM models
5. **File Handling**: Result download and log access
6. **Scalable Design**: Prepared for database integration and multi-user support

## 🔧 Configuration Options

### Server Settings

- `SERVER_HOST`: Server bind address (default: 0.0.0.0)
- `SERVER_PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (default: false)

### Model Configuration

- `DEFAULT_MODEL`: Default LLM model for experiments
- `DEFAULT_CODE_MODEL`: Default code generation model
- `OLLAMA_BASE_URL`: Ollama server URL

### Storage Settings

- `RESULTS_DIR`: Directory for experiment results
- `UPLOAD_DIR`: Directory for file uploads
- `MAX_UPLOAD_SIZE`: Maximum upload file size

### External Services

- `REDIS_URL`: Redis connection for caching/sessions
- `DATABASE_URL`: Database connection string
- `ALLOWED_HOSTS`: CORS allowed origins

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
```bash
# Check if port is already in use
netstat -an | findstr :8000

# Try a different port
uvicorn app.main:app --port 8001
```

**Ollama model not available:**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

**WebSocket connection fails:**
- Check firewall settings
- Verify WebSocket is enabled in reverse proxy (if using)
- Check browser console for CORS issues

### Performance Optimization

1. **Enable Redis**: For better WebSocket and caching performance
2. **Use PostgreSQL**: For production database requirements
3. **Configure Reverse Proxy**: Use Nginx for static files and SSL
4. **Resource Limits**: Set appropriate limits for experiment parallelism

## 🚀 Production Deployment

### Using Docker

```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/internagent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=internagent
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:alpine
```

### Environment Variables for Production

```env
DEBUG=false
SECRET_KEY=your-production-secret-key-very-long-and-random
DATABASE_URL=postgresql://user:password@localhost/internagent
ALLOWED_HOSTS=["https://yourdomain.com"]
```

## 📚 Next Steps

1. **Frontend Integration**: Connect your preferred frontend framework
2. **Authentication**: Implement proper user authentication
3. **Database Setup**: Configure persistent storage
4. **Monitoring**: Add logging and metrics collection
5. **Security**: Implement rate limiting and input validation

For more detailed examples and advanced configurations, see the API documentation at `/docs` when the server is running.