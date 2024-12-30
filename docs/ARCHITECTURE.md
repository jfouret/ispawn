# Project Architecture

## Overview

ispawn is organized following a layered architecture pattern with clear separation of concerns:

```
ispawn/
├── domain/         # Core business logic and data models
├── services/       # Business operations and external integrations
├── commands/       # CLI command implementations
├── templates/      # Jinja2 templates for Docker configs
└── files/         # Static configuration files
```

## Layers

### Domain Layer (`domain/`)

The domain layer contains the core business logic and data models. These are pure Python classes that don't depend on external services or frameworks:

- `container.py`: Models for container configuration and management
- `image.py`: Models for Docker image building and configuration
- `security.py`: Security-related utilities (password generation, etc.)
- `exceptions.py`: Custom exception classes

Domain models are designed to be:
- Independent of external services
- Focused on business rules
- Highly testable
- Free of side effects

### Service Layer (`services/`)

Services implement operations that often involve external systems or side effects:

- `docker.py`: Docker API interactions (networks, containers, images)
- `certificate.py`: SSL certificate management (mkcert, Let's Encrypt)
- `image.py`: Docker image building and management

Services are responsible for:
- Integrating with external systems
- Implementing complex operations
- Managing resources
- Handling errors and retries

### Command Layer (`commands/`)

Commands implement the CLI interface, coordinating between services to accomplish user tasks:

- `setup.py`: Environment setup (networks, certificates)
- `run.py`: Container creation and management
- `image.py`: Image building and management
- `logs.py`: Log viewing and management

Commands:
- Parse user input
- Coordinate between services
- Handle user feedback
- Manage configuration

## Key Design Principles

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

4. **Configuration**
   - Templates for dynamic configs
   - Static files for base configs
   - Environment-based settings

## Testing Strategy

See [TESTING.md](../tests/README.md) for detailed testing information.
