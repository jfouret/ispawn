# ispawn

ispawn is a command-line tool that makes it easy to create and manage Docker containers with multiple development services. With a single command, you can spin up a container running VSCode, RStudio, and Jupyter Notebook, all accessible through your web browser.

## Features

- **🚀 Quick Setup**: Get started with a single command to set up your development environment
- **🔧 Multiple Services**: Run VSCode, RStudio, and Jupyter (default) in one container. Other variants like JupyterLab and JupyterHub are also available.
- **🔒 Secure Access**: Automatic HTTPS setup with traefik reverse proxy
- **📁 Volume Mapping**: Easy mounting of local directories
- **🔄 Container Management**: Simple commands to manage your containers
- **🛠️ Build Customization**: Configure custom Dockerfile and entrypoint modifications globally
- **👥 Access Control**: Group-based access control for RStudio
- **💾 Data Persistence**: Service-specific data persistence with proper isolation

## Requirements

- Python >=3.10
- Docker
- Git (for installation from GitHub)
- Linux/Unix system (Windows support through WSL2)

## Installation

### From GitHub (Recommended)

```bash
pip install git+https://github.com/jfouret/ispawn.git
```

### From Source

```bash
git clone https://github.com/jfouret/ispawn.git
cd ispawn
pip install .
```

### Dependencies

The following Python packages will be automatically installed:
- click: Command line interface creation
- docker: Docker API interaction
- pyyaml: YAML configuration handling
- jinja2: Template processing
- tabulate: Table formatting for listings

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

The setup command configures your system with a traefik reverse proxy and build settings:

```bash
ispawn setup [OPTIONS]
```

Basic Options:
- `--domain`: Domain name for services (default: ispawn.localhost)
- `--mode`: Access mode - local or remote (default: local)
- `--cert-mode`: If remote, certificate mode (letsencrypt or provided)
- `--cert-dir`: Directory containing SSL certificate and key
- `--email`: Email for Let's Encrypt certificates
- `--subnet`: Docker network subnet (default: 172.30.0.0/24)

Build Customization Options:
- `--env-chunk-path`: Path to environment file to include in all builds
- `--dockerfile-chunk-path`: Path to Dockerfile chunk to add to all builds
- `--entrypoint-chunk-path`: Path to entrypoint script to add to all containers

Example with build customization:
```bash
ispawn setup \
  --domain dev.local \
  --env-chunk-path /path/to/env.txt \
  --dockerfile-chunk-path /path/to/custom.dockerfile \
  --entrypoint-chunk-path /path/to/startup.sh
```

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
- `--group`: Required group for RStudio access (defaults to username)

Example with custom volumes and group access:
```bash
ispawn run --name datascience --base ubuntu:22.04 \
  --volume ~/projects:/mnt/projects \
  --group data-scientists
```

### Managing Containers

List running containers:
```bash
ispawn list
```

Stop containers:
```bash
ispawn stop [CONTAINER_NAMES...] [--all] [--remove]
```
Options:
- `CONTAINER_NAMES...`: Specific container names or IDs to stop.
- `--all`: Stop all running ispawn containers.
- `--remove`: Remove the container(s) after stopping.

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

## Build Customization

You can customize how images are built by providing additional files during setup:

1. Environment File (`--env-chunk-path`):
   - Added to /etc/environment in all containers
   - Useful for setting global environment variables

2. Dockerfile Chunk (`--dockerfile-chunk-path`):
   - Added to Dockerfile during build
   - Can install additional packages or make system modifications

3. Entrypoint Script (`--entrypoint-chunk-path`):
   - Added to container entrypoint
   - Runs when container starts
   - Useful for runtime configuration

Example files:

`env.txt`:
```bash
CUSTOM_VAR=value
PROXY_SERVER=proxy.company.com
```

`custom.dockerfile`:
```dockerfile
RUN apt-get update && apt-get install -y \
    custom-package \
    another-package
```

`startup.sh`:
```bash
#!/bin/bash
echo "Configuring system..."
custom-setup-command
```

## Access Control

### RStudio Group Access

RStudio access can be restricted to specific groups:

- By default, only the user running the container can access RStudio
- Use `--group` to specify a required group for access
- Users must belong to the specified group to log in
- Useful for team-based access control

Example restricting access to data scientists:
```bash
ispawn run --name analysis --base ubuntu:22.04 --group data-scientists
```

## Data Persistence

Each service maintains its own persistent data directory for configuration and user data:

### Service-Specific Volumes

1. RStudio:
   - `~/.local/share/rstudio`: RStudio user settings and history
   - Mounted at end for proper overlay
   - Persists between container restarts

2. Jupyter:
   - `~/.jupyter`: Jupyter configuration
   - `~/.ipython`: IPython history and settings
   - Maintains notebook settings and kernels

3. VSCode:
   - `~/.vscode`: VSCode user settings
   - `~/.config/Code`: VSCode extensions and configuration
   - Preserves extensions and preferences

### Volume Organization

- Each container gets its own volume directory
- Service data is isolated in service-specific subdirectories
- Volumes are mounted in correct order for proper overlay
- Data persists even when containers are removed

Example directory structure:
```
~/.ispawn/user/ispawn/volumes/
├── container-name/
│   ├── rstudio/
│   │   └── share/
│   ├── jupyter/
│   │   ├── jupyter/
│   │   └── ipython/
│   └── vscode/
│       ├── vscode/
│       └── config/
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

4. **RStudio Access Denied**
   - Verify you belong to the required group
   - Check the group name matches exactly
   - Use `groups` command to list your groups

5. **Data Persistence Issues**
   - Check volume directory permissions
   - Verify service directories exist
   - Ensure proper overlay mounting order

### Getting Help

- Check the [GitHub Issues](https://github.com/jfouret/ispawn/issues) for known problems
- For development-related questions, see [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT License - see [LICENSE.txt](LICENSE.txt) for details
