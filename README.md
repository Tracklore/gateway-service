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
uvicorn app.main:app --reload
```

The service will be available at `http://localhost:8000`

### Production Mode

```bash
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

- `GET|POST|PUT|DELETE /user/{path}` - Routes to User Service
- `GET|POST|PUT|DELETE /auth/{path}` - Routes to Auth Service

## Configuration

The service can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| USER_SERVICE_URL | URL of the User Service | http://user-service:8000 |
| AUTH_SERVICE_URL | URL of the Auth Service | http://auth-service:8000 |
| JWT_SECRET_KEY | Secret key for JWT signing | your-super-secret-jwt-key |

## Testing

Run the test suite with pytest:

```bash
pytest
```

For test coverage:

```bash
pytest --cov=app
```

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
