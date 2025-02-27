# Core Application Documentation

## Overview

The core application module is the entry point for the Neighbour Approved API. It initializes the FastAPI application and configures it with the appropriate settings, middleware, and routers.

## Components

### Main Application (`app/main.py`)

The `main.py` file creates and configures the FastAPI application instance. It:

- Initializes the FastAPI application with metadata
- Includes API routers from various modules
- Sets up CORS, middleware, and exception handlers
- Configures OpenAPI documentation

### Usage

To start the application:

```bash
uvicorn app.main:app --reload
```

### Configuration

The application uses the following configuration:

- **Title**: "Neighbour Approved API"
- **Description**: "API for Neighbour Approved platform"
- **Version**: "0.1.0"

### Router Integration

The application integrates various routers to handle different API endpoints. Routers are included with a prefix that reflects their path in the API structure:

```python
app.include_router(health_router, prefix="/api/v1/system")
```

### Extension

To add new functionality to the application:

1. Create a new router in the appropriate module
2. Include the router in `main.py` with the correct prefix
3. Ensure proper documentation for all endpoints

## Best Practices

When extending the main application:

- Keep the main application file focused on initialization and configuration
- Move business logic to appropriate service modules
- Use dependency injection for service access
- Ensure all routes follow the established API design patterns
- Document all configuration options and their effects
