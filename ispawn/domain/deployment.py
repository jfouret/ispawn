from enum import Enum
from typing import Optional

class Mode(str, Enum):
    """Available deployment modes."""
    LOCAL = "local"   # Local development with mkcert wildcard SSL
    REMOTE = "remote" # Remote deployment with wildcard SSL (Let's Encrypt or provided)

    @classmethod
    def from_str(cls, value: str) -> "Mode":
        """Create Mode from string."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid mode: {value}. Must be one of: {' '.join(m.value for m in Mode)}")

class CertMode(str, Enum):
    """Available certificate modes for remote deployment."""
    LETSENCRYPT = "letsencrypt"  # Use Let's Encrypt for certificates
    PROVIDED = "provided"        # Use provided wildcard certificates

    @classmethod
    def from_str(cls, value: str) -> "CertMode":
        """Create CertMode from string."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid certificate mode: {value}. Must be one of: {' '.join(m.value for m in CertMode)}")

class DeploymentConfig:
    """Configuration for deployment mode and SSL certificates."""
    
    def __init__(
        self,
        mode: str = Mode.LOCAL.value,
        domain: str = "ispawn.localhost",
        subnet: str = "172.30.0.0/24",
        cert_mode: Optional[str] = None,
        cert_dir: Optional[str] = None,
        email: Optional[str] = None
    ):
        """Initialize deployment configuration.
        
        Args:
            mode: Deployment mode (local or remote)
            domain: Domain name for services
            subnet: Docker network subnet
            cert_mode: Certificate mode for remote deployment
            cert_dir: Directory for SSL certificates
            email: Email for Let's Encrypt
        """
        self.mode = Mode.from_str(mode)
        self.domain = domain
        self.subnet = subnet
        
        # Certificate configuration
        if cert_mode is not None:
            self.cert_mode = CertMode.from_str(cert_mode)
        else:
            self.cert_mode = CertMode.LETSENCRYPT if self.mode == Mode.REMOTE else None
            
        self.cert_dir = cert_dir
        self.email = email if self.mode == Mode.REMOTE else None

    @property
    def is_local(self) -> bool:
        """Check if running in local mode."""
        return self.mode == Mode.LOCAL

    @property
    def requires_email(self) -> bool:
        """Check if email is required for certificate configuration."""
        return self.mode == Mode.REMOTE and self.cert_mode == CertMode.LETSENCRYPT
