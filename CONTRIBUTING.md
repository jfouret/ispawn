# Contributing to ispawn

This guide is for developers who want to contribute to ispawn. For user documentation, see [README.md](README.md).

## Development Setup

### Requirements

- Python 3.8+
- Docker
- Development dependencies: `pip install -e ".[dev,test]"`

### Project Structure

```
ispawn/
├── domain/         # Core business logic and data models
│   ├── container.py  # Container configuration and management
│   ├── image.py      # Docker image building and configuration
│   ├── security.py   # Security utilities
│   └── exceptions.py # Custom exceptions
├── services/       # Business operations and external integrations
│   ├── docker.py     # Docker API interactions
│   ├── certificate.py # SSL certificate management
│   └── image.py      # Image building and management
├── templates/      # Jinja2 templates for Docker configs
└── files/         # Static configuration files
```

## Architecture

### Overview

ispawn follows a layered architecture pattern with clear separation of concerns:

### Domain Layer (`domain/`)

The domain layer contains the core business logic and data models. These are pure Python classes that don't depend on external services or frameworks.

Domain models are designed to be:
- Independent of external services
- Focused on business rules
- Highly testable
- Free of side effects

### Service Layer (`services/`)

Services implement operations that often involve external systems or side effects:

Services are responsible for:
- Integrating with external systems
- Implementing complex operations
- Managing resources
- Handling errors and retries

### Key Design Principles

1. **Separation of Concerns**
   - Domain models focus on business logic
   - Services handle external integrations
   - Commands coordinate operations

2. **Dependency Direction**
   ```
   commands → services → domain
   ```
   - Domain has no external dependencies
   - Services depend on domain
   - Commands depend on services and domain

3. **Error Handling**
   - Domain defines custom exceptions
   - Services translate external errors
   - Commands present errors to users

## Testing

### Running Tests

```bash
# Run unit tests
pytest

# Run with coverage
pytest --cov=ispawn

# Run integration tests
pytest -m integration

# Run end-to-end tests
pytest -m e2e
```

### Testing Strategy

Tests are organized in multiple layers:

1. **Unit Tests**
   - Test individual components in isolation
   - Mock external dependencies
   - Focus on business logic

2. **Integration Tests**
   - Test interaction between components
   - Use real Docker daemon
   - Verify service integration

3. **End-to-End Tests**
   - Test complete workflows
   - Simulate real user scenarios
   - Verify system behavior

## Contributing Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite to ensure everything passes
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Create a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for public functions
- Keep functions focused and small
- Add comments for complex logic

### Pull Request Process

1. Update documentation for any changed functionality
2. Add tests for new features
3. Update CHANGELOG.md if applicable
4. Ensure CI passes all checks
5. Get review from maintainers

## License

This project is licensed under the MIT License - see [LICENSE.txt](LICENSE.txt) for details.
