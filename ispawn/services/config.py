"""Configuration manager for ispawn."""

import os
import docker
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from ispawn.domain.config import Config
from ispawn.domain.exceptions import ConfigurationError


class ConfigManager:
    """Configuration manager for ispawn."""

    def __init__(self, config: Config, force: bool = False):
        """Initialize configuration manager.

        Args:
            config: Proxy configuration to apply
            force: Whether to force overwrite existing config

        Raises:
            ConfigurationError: If configuration is invalid or cannot be applied
        """
        self.config = config
        self.is_root = os.geteuid() == 0
        self.docker_client = docker.from_env()
        self.compose_path = str(
            Path(self.config.config_dir) / "traefik-compose.yml"
        )
        self.traefik_config_path = str(
            Path(self.config.config_dir) / "traefik.yml"
        )
        self.force = force

        # Setup Jinja environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Validate system installation requirements
        if config.is_system_install and not self.is_root:
            raise ConfigurationError(
                "Root privileges required for system-wide installation"
            )

    def _generate_ssl_certificates(self) -> None:
        """Generate SSL certificates based on configuration mode.

        Raises:
            ConfigurationError: If certificate generation fails
        """
        cert_dir = Path(self.config.cert_dir)
        cert_dir.mkdir(parents=True, exist_ok=True)

        if self.config.is_local:
            subprocess.run(
                ["mkcert", "-install"], check=True, capture_output=True
            )
            subprocess.run(
                [
                    "mkcert",
                    "-cert-file",
                    str(cert_dir / "cert.pem"),
                    "-key-file",
                    str(cert_dir / "key.pem"),
                    f"*.{self.config.domain}",
                    self.config.domain,
                ],
                check=True,
                capture_output=True,
            )

    def _generate_traefik_config(self) -> None:
        """Generate traefik configuration files."""
        # Load and render traefik compose template
        compose_template = self.jinja_env.get_template("traefik_compose.yml.j2")
        compose_config = compose_template.render(
            name=self.config.name,
            mode=self.config.mode,
            network_name=self.config.network_name,
            cert_mode=self.config.cert_mode,
            cert_dir=self.config.cert_dir,
            subnet=self.config.subnet,
        )
        # Save compose file
        with open(self.compose_path, "w") as f:
            f.write(compose_config)

        treafik_template = self.jinja_env.get_template("traefik.yml.j2")
        traefik_config = treafik_template.render(
            email=self.config.email, cert_mode=self.config.cert_mode
        )
        # Save traefik config file
        with open(self.traefik_config_path, "w") as f:
            f.write(traefik_config)

        # Copy shared providers dynamic config if using mkcert or provided certs
        if self.config.is_local or (
            self.config.mode == "remote" and self.config.cert_mode == "provided"
        ):
            shared_providers_path = (
                Path(__file__).parent.parent
                / "files"
                / "shared_providers_dynamic.yml"
            )
            target_path = (
                Path(self.config.config_dir) / "shared_providers_dynamic.yml"
            )
            with (
                open(shared_providers_path, "r") as src,
                open(target_path, "w") as dst,
            ):
                dst.write(src.read())

    def apply_config(self) -> None:
        """Apply the configuration.

        Creates necessary directories, generates certificates,
        sets up Docker network, and configures traefik.

        Raises:
            ConfigurationError: If configuration cannot be applied
        """
        # Create config directory
        config_dir = Path(self.config.config_dir)
        config_dir.mkdir(parents=True, exist_ok=True)

        # Check if config exists and compare
        write_config = True
        if os.path.exists(self.config.config_path):
            write_config = False
            with open(self.config.config_path) as f:
                existing_config = Config.from_yaml(f)
                if existing_config != self.config and self.force:
                    write_config = True
                elif existing_config != self.config and not self.force:
                    raise ConfigurationError(
                        "Configuration mismatch. Use force=True to overwrite existing config."
                    )
        if write_config:
            with open(self.config.config_path, "w") as f:
                self.config.to_yaml(f)

        # Set appropriate permissions
        if self.config.is_system_install:
            os.chmod(self.config.config_path, 0o644)  # World readable
            os.chown(self.config.config_path, 0, 0)  # Root owned
        else:
            os.chmod(self.config.config_path, 0o600)  # User readable only

        # Setup infrastructure
        if self.config.is_local:
            self._generate_ssl_certificates()
        self._generate_traefik_config()

        subprocess.run(
            ["docker", "compose", "-f", "traefik-compose.yml", "up", "-d"],
            check=True,
            cwd=self.config.config_dir,
        )

    def remove_config(self) -> None:
        """Remove the configuration and cleanup resources."""
        subprocess.run(
            ["docker", "compose", "-f", "traefik-compose.yml", "down"],
            check=True,
            cwd=self.config.config_dir,
        )
