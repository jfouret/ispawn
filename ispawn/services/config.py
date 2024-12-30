import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from ispawn.domain.deployment import Mode, CertMode, DeploymentConfig
from ispawn.domain.exceptions import ConfigurationError

class Config:
    """Configuration manager for ispawn."""

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_file: Path to configuration file. If not provided,
                        uses default location ~/.config/ispawn/config.yml
        """
        if config_file is None:
            config_file = Path.home() / ".config" / "ispawn" / "config.yml"
        
        self.config_file = config_file
        self.config_dir = config_file.parent
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create configuration
        if self.config_file.exists():
            self._load_config()
        else:
            self._create_default_config()

    def _create_default_config(self):
        """Create default configuration."""
        self.config = {
            "name": "ispawn",
            "web": {
                "domain": "ispawn.localhost",
                "subnet": "172.30.0.0/24",
                "mode": Mode.LOCAL.value,
                "ssl": {
                    "cert_dir": str(self.config_dir / "certs"),
                    "cert_mode": CertMode.LETSENCRYPT.value,
                    "email": None  # Required for Let's Encrypt
                }
            },
            "logs": {
                "dir": str(self.config_dir / "logs")
            },
            "services": {
                "jupyter": {
                    "enabled": True,
                    "port": 8888
                },
                "rstudio": {
                    "enabled": True,
                    "port": 8787
                },
                "vscode": {
                    "enabled": True,
                    "port": 8842
                }
            }
        }
        self.save()

    def _load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file) as f:
                self.config = yaml.safe_load(f) or {}
            
            # Add logs section if not present
            if "logs" not in self.config:
                self.config["logs"] = {
                    "dir": str(self.config_dir / "logs")
                }
            
            # Add SSL section if not present
            if "web" not in self.config:
                self.config["web"] = {}
            if "ssl" not in self.config["web"]:
                self.config["web"]["ssl"] = {
                    "cert_dir": str(self.config_dir / "certs"),
                    "cert_mode": CertMode.LETSENCRYPT.value,
                    "email": None
                }
            
            # Add services section if not present
            if "services" not in self.config:
                self.config["services"] = {
                    "jupyter": {
                        "enabled": True,
                        "port": 8888
                    },
                    "rstudio": {
                        "enabled": True,
                        "port": 8787
                    },
                    "vscode": {
                        "enabled": True,
                        "port": 8842
                    }
                }
            
            self.save()
                
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid configuration file: {str(e)}")

    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f)
            
            # Ensure config file is only readable by owner
            os.chmod(self.config_file, 0o600)
        except (OSError, IOError) as e:
            raise ConfigurationError(f"Failed to save configuration: {str(e)}")

    @property
    def name(self) -> str:
        """Get project name."""
        return self.config.get("name", "ispawn")

    @property
    def deployment(self) -> DeploymentConfig:
        """Get deployment configuration."""
        web_config = self.config.get("web", {})
        ssl_config = web_config.get("ssl", {})
        
        return DeploymentConfig(
            mode=web_config.get("mode", Mode.LOCAL.value),
            domain=web_config.get("domain", "ispawn.localhost"),
            subnet=web_config.get("subnet", "172.30.0.0/24"),
            cert_mode=ssl_config.get("cert_mode"),
            cert_dir=ssl_config.get("cert_dir"),
            email=ssl_config.get("email")
        )

    @property
    def network_name(self) -> str:
        """Get Docker network name."""
        return self.name

    @property
    def log_dir(self) -> Path:
        """Get log directory path."""
        return Path(self.config.get("logs", {}).get("dir", str(self.config_dir / "logs")))

    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration."""
        return self.config.copy()  # Return a copy to prevent modification

    def get_service_config(self, service: str) -> Dict[str, Any]:
        """Get service configuration.
        
        Args:
            service: Service name
            
        Returns:
            Service configuration dictionary
            
        Raises:
            ConfigurationError: If service doesn't exist
        """
        if service not in self.config.get("services", {}):
            raise ConfigurationError(f"Service '{service}' not found in configuration")
        return self.config["services"][service].copy()  # Return a copy to prevent modification

    def set_mode(self, mode: str):
        """Set deployment mode."""
        try:
            mode_enum = Mode.from_str(mode)
            if "web" not in self.config:
                self.config["web"] = {}
            self.config["web"]["mode"] = mode_enum.value
            self.save()
        except ValueError as e:
            raise ConfigurationError(str(e))

    def set_cert_mode(self, mode: str):
        """Set certificate mode."""
        try:
            mode_enum = CertMode.from_str(mode)
            if "web" not in self.config:
                self.config["web"] = {}
            if "ssl" not in self.config["web"]:
                self.config["web"]["ssl"] = {}
            self.config["web"]["ssl"]["cert_mode"] = mode_enum.value
            self.save()
        except ValueError as e:
            raise ConfigurationError(str(e))

    def set_domain(self, domain: str):
        """Set domain name."""
        if "web" not in self.config:
            self.config["web"] = {}
        self.config["web"]["domain"] = domain
        self.save()

    def set_subnet(self, subnet: str):
        """Set subnet configuration."""
        if "web" not in self.config:
            self.config["web"] = {}
        self.config["web"]["subnet"] = subnet
        self.save()

    def set_log_dir(self, log_dir: Path):
        """Set log directory path."""
        if "logs" not in self.config:
            self.config["logs"] = {}
        self.config["logs"]["dir"] = str(log_dir)
        self.save()

    def set_cert_dir(self, cert_dir: Path):
        """Set SSL certificate directory."""
        if "web" not in self.config:
            self.config["web"] = {}
        if "ssl" not in self.config["web"]:
            self.config["web"]["ssl"] = {}
        self.config["web"]["ssl"]["cert_dir"] = str(cert_dir)
        self.save()

    def set_email(self, email: str):
        """Set email for Let's Encrypt."""
        if "web" not in self.config:
            self.config["web"] = {}
        if "ssl" not in self.config["web"]:
            self.config["web"]["ssl"] = {}
        self.config["web"]["ssl"]["email"] = email
        self.save()
