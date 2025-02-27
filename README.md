# Neighbour Approved

[![CI](https://github.com/47products/Neighbour-Approved/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/47products/Neighbour-Approved/actions/workflows/ci.yml)

**Neighbour Approved** is a community-driven platform designed to help residents within a community endorse and share trusted contacts (such as contractors or service providers) in a public, easily accessible way. It aims to streamline what often happens in community WhatsApp groups: repeated sharing of the same contacts as members join, leave, or request recommendations.

## Vision and Purpose

- **Community-Driven:** Allow residents in a particular community to upload, endorse, and share contact details of contractors or service providers (e.g., plumbers, electricians, painters).
- **Publicly Available:** Enable public viewing for approved communities, so non-residents can discover reputable service providers.
- **Scalability:** Communities can link to neighbouring communities, share their trusted contacts, and strengthen their network.
- **Subscription & Sponsorship Model:** Communities can register freely with limited functionality, and upgrade to paid subscription plans for advanced features. Contractors can sponsor communities for advertising opportunities.

## Tech Stack & Approach

- **Language & Framework:** Python with FastAPI for a high-performance, asynchronous backend.
- **Architecture & Structure:**
  - A layered, service-oriented architecture with clear separation of concerns (API layer, domain/business logic, data layer, and infrastructure).
  - TDD (Test-Driven Development) approach to ensure code quality and maintainability.
- **Testing & Quality:**
  - `pytest` for testing, `pytest-asyncio` for async tests.
  - `black` and `pylint` for formatting and linting.
  - `coverage.py` to ensure 80%+ test coverage.
- **Modern Practices:**
  - Follow Conventional Commits for commit messages and PR naming to ensure clarity and facilitate automated changelogs.
  - Use of a virtual environment (`venv`) to isolate project dependencies.
  - Documentation through docstrings, auto-generated OpenAPI/Swagger for API endpoints, and well-structured `README` and `CONTRIBUTING` files.

## CI/CD Setup

**Continuous Integration (CI)** is handled by GitHub Actions. On every push or pull request to `main`, a workflow runs that:

1. **Checks out the code** and sets up the Python environment.
2. **Creates a virtual environment** (`venv`) for dependency isolation.
3. **Installs dependencies** from `requirements.txt`.
4. **Runs Quality Checks:**
   - **Black**: Ensures code formatting standards are met (`black --check .`).
   - **Pylint**: Performs static code analysis to detect issues (`pylint app tests`).
5. **Runs Tests with Coverage:**
   - Executes `pytest` with `coverage` to run test suites and measure code coverage.
   - Fails if coverage is below 80%, ensuring a high standard of testing.
   - Generates HTML coverage reports and uploads them as workflow artifacts.

**Continuous Delivery (CD)** can be integrated in the future to automatically deploy the application once the CI checks pass, ensuring a reliable and seamless release process.

### Status Badge

The status badge at the top of this `README` reflects the current build status of the CI pipeline. This provides immediate feedback to contributors and maintainers, ensuring code quality and preventing merges that would break the build.

## Getting Started

**Prerequisites:**

- Python 3.12 (or as specified in the workflow)
- A Python virtual environment for isolation

**Setup Steps:**

1. Clone the repository:

   ```bash
   git clone https://github.com/47products/Neighbour-Approved.git
   cd Neighbour-Approved
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Run tests and linting locally:

   ```bash
   black --check .
   pylint app tests
   coverage run -m pytest
   coverage report --fail-under=80
   ```

## Commit & PR Guidelines

- **Conventional Commits:**  
  Use `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore` in commit messages.
  Example: `feat(auth): add OAuth2 login support`
- **PR Titles:**  
  Short and descriptive, possibly referencing an issue or story ID.  
  Example: `[NEI-24] feat(auth): implement OAuth2 login`

## Future Plans

- **Integrate with External APIs:**  
  Potential integration with WhatsApp APIs for automated community responses.
- **Microservices & Event-Driven Architecture:**  
  As the platform scales, consider breaking out services and using event-driven patterns.
- **Refined Subscription & Sponsorship Models:**  
  Implementing tiered subscription plans and managing sponsorship relationships for communities and contractors.

**Neighbour Approved** will continue to evolve with a focus on community needs, code quality, and operational excellence. The project’s CI/CD pipeline and development best practices ensure it remains robust, maintainable, and ready for future growth.
