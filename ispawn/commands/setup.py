import os
from pathlib import Path
from typing import Optional
import shutil
import jinja2
from ispawn.config import Config, Mode, CertMode
from ispawn.services.docker import DockerService
from ispawn.services.certificate import CertificateService
from ispawn.domain.exceptions import ConfigurationError, CertificateError

def render_template(template_path: Path, output_path: Path, context: dict) -> None:
    """Render a Jinja2 template to a file."""
    try:
        template_dir = template_path.parent
        template_name = template_path.name
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_dir)))
        template = env.get_template(template_name)
        content = template.render(**context)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        
    except (jinja2.TemplateError, OSError) as e:
        raise RuntimeError(f"Failed to render template {template_path}: {str(e)}")

def setup_traefik(config: Config) -> None:
    """Setup Traefik reverse proxy configuration."""
    # Get package directory
    package_dir = Path(__file__).parent.parent
    
    # Render compose file
    template_path = package_dir / "templates/traefik_compose.yml.j2"
    output_path = config.config_dir / "traefik-compose.yml"
    
    # Create template context
    context = {
        "network_name": config.network_name,
        "domain": config.domain,
        "mode": config.mode.value,
        "cert_mode": config.cert_mode.value,
        "cert_dir": config.cert_dir,
        "email": config.email
    }
    
    render_template(template_path, output_path, context)

def setup_environment(config: Config, env_file: Optional[Path] = None) -> None:
    """Setup environment configuration."""
    if env_file:
        dst = config.config_dir / ".env"
        shutil.copy2(env_file, dst)

def setup_logs(config: Config) -> None:
    """Setup log directory structure."""
    log_dir = config.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set permissions: readable only by owner
    os.chmod(log_dir, 0o700)
    
    # Create README file
    readme = log_dir / "README.md"
    readme.write_text("""# ispawn Logs Directory

This directory contains logs from ispawn containers. Each container gets its own
numbered subdirectory (e.g., container-name.1, container-name.2, etc.).

## Directory Structure

```
container-name.1/
  ├── entrypoint.log  # Container startup and service initialization logs
  ├── jupyter/        # Jupyter service logs (if enabled)
  ├── rstudio/        # RStudio service logs (if enabled)
  └── vscode/         # VS Code service logs (if enabled)
```

The numbered directories help maintain history when containers are recreated.
""")

def setup_certificates(config: Config, cert_service: CertificateService) -> None:
    """Setup SSL certificates based on mode and certificate type."""
    if config.mode == Mode.LOCAL:
        cert_service.setup_local_certificates(config.domain, config.cert_dir)
    elif config.mode == Mode.REMOTE:
        if config.cert_mode == CertMode.PROVIDED:
            cert_service.validate_certificates(config.cert_dir)
        else:  # CertMode.LETSENCRYPT
            if not config.email:
                raise CertificateError("Email is required for Let's Encrypt certificates")
            cert_service.setup_remote_certificates(config.cert_dir, config.email)

def setup_command(config: Config, mode: Optional[str] = None, domain: Optional[str] = None,
                 subnet: Optional[str] = None, cert_mode: Optional[str] = None,
                 email: Optional[str] = None, env_file: Optional[Path] = None) -> None:
    """Setup ispawn environment.
    
    Args:
        config: Configuration instance
        mode: Deployment mode (local or remote)
        domain: Domain name
        subnet: Subnet configuration
        cert_mode: Certificate mode (letsencrypt or provided)
        email: Email for Let's Encrypt
        env_file: Path to environment file
        
    Raises:
        ConfigurationError: If configuration is invalid
        RuntimeError: If setup fails
    """
    try:
        # Update configuration if provided
        if mode:
            config.set_mode(mode)
        if domain:
            config.set_domain(domain)
        if subnet:
            config.set_subnet(subnet)
        if cert_mode:
            config.set_cert_mode(cert_mode)
        if email:
            config.set_email(email)
        
        # Initialize services
        docker_service = DockerService()
        cert_service = CertificateService()
        
        # Setup network
        docker_service.ensure_network(config.network_name, config.subnet)
        
        # Setup logs directory
        setup_logs(config)
        
        # Setup SSL certificates
        setup_certificates(config, cert_service)
        
        # Setup Traefik
        setup_traefik(config)
        
        # Setup environment if provided
        if env_file:
            setup_environment(config, env_file)
            
    except (ConfigurationError, CertificateError) as e:
        raise ConfigurationError(str(e))
    except Exception as e:
        raise RuntimeError(f"Setup failed: {str(e)}")
