# Gateway Service

The single entry point for the entire Tracklore platform. This microservice routes all incoming requests to the correct backend services, centralizes JWT authentication and authorization, and provides a stable, scalable interface for the frontend to interact with.

## Features

- **API Gateway**: Centralized routing to backend microservices
- **JWT Authentication**: Secure token-based authentication
- **Circuit Breaker Pattern**: Prevents cascading failures
- **CORS Support**: Cross-origin resource sharing for frontend integration
- **Health Checks**: Service status monitoring
- **Error Handling**: Graceful error handling for downstream service failures
- **Logging**: Comprehensive request and error logging

## Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)
- pip (Python package installer)

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gateway-service
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Configure the environment variables in the `.env` file as needed.

## Running the Service

### Development Mode

```bash
# Using the run script (automatically activates virtual environment)
./run.sh

# Or manually:
uvicorn app.main:app --reload
```

The service will be available at `http://localhost:8000`

### Production Mode

```bash
# Using the run script (automatically activates virtual environment)
./run.sh

# Or manually:
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Using Docker

```bash
docker build -t gateway-service .
docker run -p 8000:8000 gateway-service
```

## API Endpoints

### Public Endpoints

- `GET /health` - Health check endpoint

### Protected Endpoints

All protected endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

- `GET|POST|PUT|DELETE /user/{path}` - Routes to User Service (port 8001)
- `GET|POST|PUT|DELETE /auth/{path}` - Routes to Auth Service (port 8002)
- `GET|POST|PUT|DELETE /badge/{path}` - Routes to Badge Service (port 8003)
- `GET|POST|PUT|DELETE /feed/{path}` - Routes to Feed Service (port 8004)
- `GET|POST|PUT|DELETE /messaging/{path}` - Routes to Messaging Service (port 8005)
- `GET|POST|PUT|DELETE /notification/{path}` - Routes to Notification Service (port 8006)
- `GET|POST|PUT|DELETE /project/{path}` - Routes to Project Service (port 8007)
- `GET|POST|PUT|DELETE /new/{path}` - Routes to New Service (port 8008)

## Configuration

The service can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| USER_SERVICE_URL | URL of the User Service | http://user-service:8001 |
| AUTH_SERVICE_URL | URL of the Auth Service | http://auth-service:8002 |
| BADGE_SERVICE_URL | URL of the Badge Service | http://badge-service:8003 |
| FEED_SERVICE_URL | URL of the Feed Service | http://feed-service:8004 |
| MESSAGING_SERVICE_URL | URL of the Messaging Service | http://messaging-service:8005 |
| NOTIFICATION_SERVICE_URL | URL of the Notification Service | http://notification-service:8006 |
| PROJECT_SERVICE_URL | URL of the Project Service | http://project-service:8007 |
| NEW_SERVICE_URL | URL of the New Service | http://new-service:8008 |
| JWT_SECRET_KEY | Secret key for JWT signing | your-super-secret-jwt-key |

## Testing

### Running Tests

The gateway service includes comprehensive tests covering unit, integration, performance, and edge cases.

Run all tests:
```bash
# Using the test script (automatically activates virtual environment)
./test.sh

# Or using the test runner
./run_tests.sh

# Or manually:
pytest
```

Run tests with coverage:
```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

Run specific test suites:
```bash
# Unit tests
pytest tests/test_routes.py tests/test_auth.py

# Integration tests
pytest tests/test_integration.py

# Performance tests
pytest tests/test_performance.py

# Edge case tests
pytest tests/test_edge_cases.py

# Circuit breaker tests
pytest tests/test_circuit_breaker.py

# Authentication utility tests
pytest tests/test_auth_utils.py
```

### Test Categories

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test the interaction between components
3. **Performance Tests**: Test the performance and scalability
4. **Edge Case Tests**: Test unusual or extreme scenarios
5. **Authentication Tests**: Test JWT token handling
6. **Circuit Breaker Tests**: Test the circuit breaker implementation

### Test Coverage

The tests cover:
- All API endpoints
- Authentication and authorization
- Error handling scenarios
- Circuit breaker functionality
- Header and body processing
- Performance under load
- Edge cases and unusual inputs
- Security considerations

## Security

- All protected endpoints require JWT authentication
- Services communicate over internal network
- Docker container runs as non-root user
- CORS is configured for secure cross-origin requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License.
