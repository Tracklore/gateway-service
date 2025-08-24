# GitHub Issues for Gateway Service

## 1. Fix Import Path in routes.py

**Description:**
The import path in `app/api/routes.py` is incorrect. It's trying to import settings from `core.settings` but should be importing from `shared_libs.core.settings`.

**Current Code:**
```python
from core.settings import settings
```

**Should Be:**
```python
from shared_libs.core.settings import settings
```

**Error:**
This causes ModuleNotFoundError when running the application.

**Labels:** bug, critical

---

## 2. Implement JWT Authentication

**Description:**
The `app/dependencies/auth.py` file is just a placeholder with no actual JWT validation logic. This is a security risk as the gateway has no authentication.

**Requirements:**
1. Implement JWT validation middleware
2. Add dependency injection for protected routes
3. Handle expired/invalid tokens appropriately

**Labels:** feature, security, critical

---

## 3. Add Error Handling to Proxy Function

**Description:**
The proxy function in `app/api/routes.py` lacks proper error handling for network failures and service unavailability.

**Requirements:**
1. Add try/except blocks for httpx requests
2. Return appropriate error responses (502/504) for downstream service failures
3. Add timeouts to prevent hanging requests
4. Log errors for debugging

**Labels:** bug, high

---

## 4. Update Pydantic Settings Configuration

**Description:**
The settings.py file uses deprecated class-based Config which is deprecated in Pydantic V2.

**Current Code:**
```python
class Config:
    env_file = ".env"
```

**Should Use:**
```python
model_config = SettingsConfigDict(env_file=".env")
```

**Labels:** enhancement, high

---

## 5. Add Service Validation

**Description:**
The proxy function doesn't validate if the requested service is supported, leading to incorrect routing.

**Requirements:**
1. Add a list of supported services
2. Return 404 for unsupported services
3. Make service routing more extensible

**Labels:** enhancement, high

---

## 6. Improve Docker Security

**Description:**
The Dockerfile runs the application as root user, which is a security risk.

**Requirements:**
1. Create a non-root user
2. Run the application with limited privileges
3. Set proper file permissions

**Labels:** security, high

---

## 7. Add Circuit Breaker Pattern

**Description:**
Add circuit breaker pattern to prevent cascading failures when downstream services are unavailable.

**Requirements:**
1. Implement circuit breaker for each service
2. Fail fast when circuits are open
3. Automatically retry after timeout

**Labels:** enhancement, medium

---

## 8. Add Comprehensive Logging

**Description:**
Add proper logging throughout the application for monitoring and debugging.

**Requirements:**
1. Log incoming requests
2. Log proxy routing decisions
3. Log errors and exceptions
4. Add request IDs for tracing

**Labels:** enhancement, medium

---

## 9. Add CORS Middleware

**Description:**
Add CORS middleware to enable frontend integration.

**Requirements:**
1. Configure CORS origins
2. Allow appropriate HTTP methods
3. Set proper headers

**Labels:** enhancement, medium

---

## 10. Improve Test Coverage

**Description:**
Current tests only cover happy paths. Need to add tests for error cases.

**Requirements:**
1. Add tests for network failures
2. Add tests for invalid service names
3. Add tests for authentication (when implemented)
4. Add tests for different HTTP methods

**Labels:** testing, medium

---

## 11. Add Health Check Endpoint Details

**Description:**
Enhance the health check endpoint to provide more detailed information.

**Requirements:**
1. Check connectivity to downstream services
2. Report service statuses
3. Add version information

**Labels:** enhancement, low

---

## 12. Improve Documentation

**Description:**
The README.md is minimal and lacks detailed usage instructions.

**Requirements:**
1. Add setup instructions
2. Add configuration details
3. Add API documentation
4. Add deployment guides

**Labels:** documentation, low

---

## 13. Pin Dependency Versions

**Description:**
The requirements.txt doesn't pin specific versions, which can lead to instability.

**Requirements:**
1. Pin all dependency versions
2. Add dependency comments
3. Consider using pip-tools for dependency management

**Labels:** enhancement, low

---

## 14. Optimize Dockerfile

**Description:**
The Dockerfile can be optimized with multi-stage builds and better layer caching.

**Requirements:**
1. Implement multi-stage build
2. Optimize copy order for better caching
3. Add Docker health checks

**Labels:** enhancement, low