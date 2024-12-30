# ispawn

ispawn is a command line tool to spawn Docker containers holding multiple services with a single command.

## Features

- **System Setup**: Configure your system with traefik reverse proxy for service access
- **Image Building**: Build Docker images with multiple services (RStudio, Jupyter, VSCode)
- **Container Management**: Run containers with automatic volume mapping and user permissions
- **Service Access**: Access services through your browser with automatic URL configuration

## Installation

```bash
pip install .
```

## Quick Start

1. Setup your system:
```bash
ispawn setup
```

2. Build an image with services:
```bash
ispawn image build --image ubuntu:20.04
```

3. Run a container:
```bash
ispawn run --name test --image ispawn-ubuntu:20.04
```

## Usage

### System Setup

Setup your system with traefik reverse proxy:

```bash
ispawn setup [--domain domain] [--mode local|remote] [--cert path] [--key path]
```

Options:
- `--domain`: Domain name for services (default: ispawn.localhost)
- `--mode`: Access mode - local or remote (default: local)
- `--cert`: Path to SSL certificate for HTTPS
- `--key`: Path to SSL private key
- `--subnet`: Docker network subnet (default: 172.30.192.0/24)

### Image Management

Build a Docker image with services:

```bash
ispawn image build --image <base-image> [--services services] [--env-file path] [--setup-file path]
```

Options:
- `--image`: Base Docker image (debian/ubuntu based)
- `--services`: Comma-separated list of services (default: rstudio,jupyter,vscode)
- `--env-file`: Environment file to include
- `--setup-file`: Setup script to run during build

List built images:
```bash
ispawn image list
```

Remove images:
```bash
ispawn image rm [--all] [image-names...]
```

### Container Management

Run a container with services:

```bash
ispawn run --name <name> --image <image> [options]
```

Options:
- `--name`: Container name
- `--image`: Docker image to use
- `--services`: Comma-separated list of services
- `--username`: Username (default: current user)
- `--password`: Password (default: generated)
- `--volumes`: Comma-separated list of volumes to mount
- `--force`: Force replace existing container

List running containers:
```bash
ispawn list
```

## Development

### Requirements

- Python 3.8+
- Docker
- Development dependencies: `pip install -e ".[dev,test]"`

### Testing

Run tests:
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

### Project Structure

```
ispawn/
├── domain/         # Domain models and business logic
│   ├── container.py
│   ├── image.py
│   └── exceptions.py
├── services/       # Service layer for external operations
│   ├── docker.py
│   └── image.py
├── commands/       # CLI commands
│   ├── image.py
│   ├── run.py
│   └── setup.py
├── templates/      # Jinja2 templates
└── files/         # Static configuration files
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Create a pull request

## License

MIT License - see LICENSE.txt for details
