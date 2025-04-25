from enum import Enum
from typing import Optional, TextIO
from ispawn.domain.exceptions import ConfigurationError
from yaml import dump, safe_load
from pathlib import Path
from typing import List

class BaseMode(str, Enum):
    """Base class for mode enums with common string conversion functionality."""
    
    @classmethod
    def from_str(cls, value: str) -> "BaseMode":
        """Create mode from string."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid {cls.__name__.lower()}: {value}. Must be one of: {' '.join(m.value for m in cls)}")

    def __str__(self) -> str:
        return self.value

class ProxyMode(BaseMode):
    """Available reverse proxy modes."""
    LOCAL = "local"   # Expose services through localhost with mkcert SSL
    REMOTE = "remote" # Expose services through domain with wildcard SSL

class CertMode(BaseMode):
    """Available certificate modes for remote proxy."""
    LETSENCRYPT = "letsencrypt"  # Use Let's Encrypt for certificates
    PROVIDED = "provided"        # Use provided wildcard certificates

class InstallMode(BaseMode):
    """Available installation modes."""
    SYSTEM = "system"  # Install system-wide
    USER = "user"      # Install for current user

class Config:
    """Configuration for reverse proxy and SSL certificates.
    
    Attrs:
      install_mode: Installation mode system or user
      mode: Proxy mode (local or remote)
      domain: Domain name for services
      subnet: Docker network subnet
      name: Base name
      network_name: Network name
      cert_mode: Certificate mode (required for remote proxy)
      cert_dir: Directory for SSL certificates
      email: Email for Let's Encrypt (required if cert_mode is letsencrypt)
      env_chunk_path: Path to environment file for Docker builds
      dockerfile_chunk_path: Path to dockerfile chunk for Docker builds
      entrypoint_chunk_path: Path to entrypoint chunk for Docker builds
    """
    
    @staticmethod
    def get_system_dir() -> str:
        """Get system-wide installation directory.
        
        Returns:
            Path to system-wide installation directory (/etc/ispawn)
        """
        return "/etc/ispawn"

    def __init__(
        self,
        install_mode: str,
        mode: str,
        domain: str,
        subnet: str,
        name: str,
        dns: List[str] = None,
        user_in_namespace: bool = False,
        cert_mode: Optional[str] = None,
        cert_dir: Optional[str] = None,
        email: Optional[str] = None,
        volumes: str = None,
        mount_point: str = None,
        env_chunk_path: Optional[str] = None,
        dockerfile_chunk_path: Optional[str] = None,
        entrypoint_chunk_path: Optional[str] = None,
        home_prefix: str = "/home/",
        timezone: str = "Europe/Paris"
    ):
        """Initialize reverse proxy configuration.
        
        Args:
            mode: Proxy mode (local or remote)
            domain: Domain name for services
            subnet: Docker network subnet
            name: Base name
            user_in_namespace: If true, add username to namespace when running container
            cert_mode: Certificate mode (required for remote proxy)
            cert_dir: Directory for SSL certificates
            email: Email for Let's Encrypt (required if cert_mode is letsencrypt)
            env_chunk_path: Path to environment file for Docker builds
            dockerfile_chunk_path: Path to dockerfile chunk for Docker builds
            entrypoint_chunk_path: Path to entrypoint chunk for Docker builds
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        
        self.mode = ProxyMode.from_str(mode)
        self.install_mode = InstallMode.from_str(install_mode)
        self.dns = dns or ["8.8.8.8", "8.8.4.4"]
        self.domain = domain
        self.subnet = subnet
        self.name = name
        self.user_in_namespace = user_in_namespace
        self.mount_point = mount_point.rstrip("/") if mount_point else ""
        self.volumes = volumes
        self.env_chunk_path = str(Path(env_chunk_path).resolve()) if env_chunk_path else None
        self.dockerfile_chunk_path = str(Path(dockerfile_chunk_path).resolve()) if dockerfile_chunk_path else None
        self.entrypoint_chunk_path = str(Path(entrypoint_chunk_path).resolve()) if entrypoint_chunk_path else None
        self.home_prefix = home_prefix.rstrip("/")
        self.timezone = timezone
        
        # Create user root directory and logs directory
        user_root = Path(self.user_root_dir)
        user_root.mkdir(parents=True, exist_ok=True)
        
        log_dir = Path(self.base_log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Certificate configuration
        if self.mode == ProxyMode.REMOTE:
            if cert_mode is None:
                raise ConfigurationError("Certificate mode is required for remote proxy")
            self.cert_mode = CertMode.from_str(cert_mode)
            
            if self.cert_mode == CertMode.LETSENCRYPT and not email:
                raise ConfigurationError("Email is required for Let's Encrypt certificates")
        else:
            # Local mode uses mkcert
            self.cert_mode = None
            if email:
                raise ConfigurationError("Email is not used in local proxy mode")
            if not self.domain.endswith(".localhost"):
                raise ConfigurationError("Domain must end with '.localhost' in local proxy mode")

        self.cert_dir = str(Path(self.config_dir) / "certs") if cert_dir is None else cert_dir
        self.email = email if self.mode == ProxyMode.REMOTE else None
    
    def to_yaml(self, fh: TextIO) -> None:
        """Serialize proxy configuration to YAML."""
        dump(
            {
                k: str(v) if isinstance(v, BaseMode) else v
                for k,v in self.__dict__.items()
            }, fh)

    def save(self) -> None:
        """Save proxy configuration to system or user configuration."""
        with open(Path(self.config_dir) / "config.yaml", "w") as fh:
            self.to_yaml(fh)

    @classmethod
    def from_yaml(cls, fh: TextIO) -> "Config":
        """Create Config from YAML."""
        data = safe_load(fh)
        return cls(**data)

    @classmethod
    def load(cls, user_mode = False) -> "Config":
        """Create Config from system configuration using from_yaml."""
        if user_mode:
            conf_path = Path.home() / ".ispawn" / "config.yaml"
        else:
            conf_path = Path("/etc/ispawn/config.yaml")
        if conf_path.exists():
            with open(conf_path, "r") as fh:
                return cls.from_yaml(fh)
        else:
            return None

    def __eq__(self, value: "Config") -> bool:
        if not isinstance(value, Config):
            print(f"{value} is not a Config")
            return False
        for k in self.__dict__.keys():
            if self.__dict__[k] != value.__dict__[k]:
                print(f"{k}: {self.__dict__[k]} != {value.__dict__[k]}")
                return False
        return True

    @property
    def is_local(self) -> bool:
        """Check if using local proxy mode."""
        return self.mode == ProxyMode.LOCAL

    @property
    def requires_email(self) -> bool:
        """Check if email is required for certificate configuration."""
        return (
            self.mode == ProxyMode.REMOTE and 
            self.cert_mode == CertMode.LETSENCRYPT
        )

    @property
    def network_name(self) -> str:
        """Get Docker network name."""
        return f"{self.name}_internal"

    @property
    def is_system_install(self) -> bool:
        """Check if using system-wide installation."""
        return self.install_mode == InstallMode.SYSTEM

    @property
    def config_dir(self) -> str:
        """Get config dir"""
        if self.is_system_install:
            return self.get_system_dir()
        return str(Path.home() / ".ispawn")

    @property
    def user_root_dir(self) -> str:
        """Get user root directory path."""
        return str(Path.home() / ".ispawn" / "user" / self.name)

    @property
    def base_log_dir(self) -> str:
        """Get base log directory path."""
        return str(Path(self.user_root_dir) / "logs")

    @property
    def image_name_prefix(self) -> str:
        """Get image name prefix"""
        return f"{self.name}-"
    
    @property
    def container_name_prefix(self) -> str:
        """Get container name prefix"""
        if self.user_in_namespace:
            return f"{self.name}-{self.user}-"
        else:
            return f"{self.name}-"

    @property
    def domain_prefix(self) -> str:
        """Get domain prefix"""
        if self.user_in_namespace:
            return f"{self.user}-"
        else:
            return ""

    @property
    def config_path(self) -> str:
        """Get config path"""
        return str(Path(self.config_dir) / "config.yaml")
