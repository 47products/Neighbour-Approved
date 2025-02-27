# Neighbour Approved Technical Guide

## Application Structure

The Neighbour Approved application follows a layered architecture pattern with clear separation of concerns:

- **API Layer**: FastAPI endpoints and request/response handling
- **Middleware Layer**: Authentication, logging, and cross-cutting concerns
- **Domain Layer**: Business logic and services
- **Data Layer**: Database models and repositories
- **Infrastructure Layer**: Configuration, security, and utilities

## Getting Started

### Running the Application

To run the application locally:

1. Ensure you have Python 3.12 installed
2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:

   ```bash
   uvicorn app.main:app --reload
   ```

### Running Tests

The application uses pytest for testing:

```bash
pytest
```

For test coverage:

```bash
coverage run -m pytest
coverage report
```

## API Documentation

When the application is running, API documentation is available at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc URL:  <http://localhost:8000/redoc>

## Development Workflow

We follow a Test-Driven Development (TDD) approach:

1. Write a failing test
2. Implement the minimal code to make the test pass
3. Refactor as needed
4. Repeat

All code should follow the project's coding standards and include appropriate
documentation as outlined in `docstring-guide.md`.

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **API Tests**: Test API endpoints end-to-end

Tests should be comprehensive and cover both success and failure cases. Each test should focus on a specific functionality or scenario.

## Best Practices

- Follow the docstring guidelines in `docstring-guide.md`
- Write clean, maintainable code with clear responsibility boundaries
- Implement proper error handling and validation
- Include comprehensive tests for all new features
- Document all API endpoints in code with proper annotations
