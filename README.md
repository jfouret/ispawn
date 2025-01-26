# ispawn

ispawn is a command-line tool that makes it easy to create and manage Docker containers with multiple development services. With a single command, you can spin up a container running VSCode, RStudio, and Jupyter Notebook, all accessible through your web browser.

## Features

- **🚀 Quick Setup**: Get started with a single command to set up your development environment
- **🔧 Multiple Services**: Run VSCode, RStudio, and Jupyter Notebook in one container
- **🔒 Secure Access**: Automatic HTTPS setup with traefik reverse proxy
- **📁 Volume Mapping**: Easy mounting of local directories
- **🔄 Container Management**: Simple commands to manage your containers

## Installation

```bash
pip install .
```

## Quick Start

1. Set up your environment (only needed once):
```bash
ispawn setup
```

2. Run a container with default services (VSCode, RStudio, Jupyter):
```bash
ispawn run --name mydev --base ubuntu:22.04
```

3. Access your services through your browser:
```
VSCode:   https://mydev-vscode.ispawn.localhost
RStudio:  https://mydev-rstudio.ispawn.localhost
Jupyter:  https://mydev-jupyter.ispawn.localhost
```

## Usage Guide

### Setting Up Your Environment

The setup command configures your system with a traefik reverse proxy for secure service access:

```bash
ispawn setup [OPTIONS]
```

Options:
- `--domain`: Domain name for services (default: ispawn.localhost)
- `--mode`: Access mode - local or remote (default: local)
- `--cert-mode`: If remote, certificate mode (letsencrypt or provided)
- `--cert-dir`: Directory containing SSL certificate and key
- `--email`: Email for Let's Encrypt certificates
- `--subnet`: Docker network subnet (default: 172.30.0.0/24)

### Running Containers

Create and start a container with development services:

```bash
ispawn run [OPTIONS]
```

Options:
- `--name`: Container name (required)
- `--base`: Base Docker image (required)
- `--service`: Services to include (defaults to vscode, rstudio, jupyter)
- `--volume`: Directories to mount (can specify multiple)
- `--build`: Build image if it doesn't exist
- `--force`: Replace existing container

Example with custom volumes:
```bash
ispawn run --name datascience --base ubuntu:22.04 --volume ~/projects:/mnt/projects
```

### Managing Containers

List running containers:
```bash
ispawn list
```

Stop containers:
```bash
ispawn stop [CONTAINER_NAMES...] [--all]
```

Remove containers:
```bash
ispawn remove [CONTAINER_NAMES...] [--all]
```

### Managing Images

Build a custom image:
```bash
ispawn build --base ubuntu:22.04 [--service SERVICE]...
```

List available images:
```bash
ispawn image list
```

Remove images:
```bash
ispawn image remove [IMAGE_IDS...] [--all]
```

## Troubleshooting

### Common Issues

1. **Certificate Errors**
   - For local development, ensure your system trusts the generated certificates
   - For remote access, verify your SSL certificates are valid

2. **Port Conflicts**
   - Ensure ports 80/443 are available for traefik
   - Check for other services using required ports

3. **Container Access**
   - Verify the container is running with `ispawn list`
   - Check your /etc/hosts file has the correct entries
   - Ensure your browser accepts the SSL certificates

### Getting Help

- Check the [GitHub Issues](https://github.com/jfouret/ispawn/issues) for known problems
- For development-related questions, see [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT License - see [LICENSE.txt](LICENSE.txt) for details
