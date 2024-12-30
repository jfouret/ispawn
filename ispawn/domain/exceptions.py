class ISpawnError(Exception):
    """Base exception for all ispawn errors."""
    pass

class ContainerError(ISpawnError):
    """Raised when there's an error with container operations."""
    pass

class ConfigurationError(ISpawnError):
    """Raised when there's an error with configuration."""
    pass

class ImageError(ISpawnError):
    """Raised when there's an error with Docker images."""
    pass

class NetworkError(ISpawnError):
    """Raised when there's an error with Docker network operations."""
    pass

class ValidationError(ISpawnError):
    """Raised when there's an error with input validation."""
    pass

class CertificateError(ISpawnError):
    """Raised when there's an error with SSL certificate operations."""
    pass
