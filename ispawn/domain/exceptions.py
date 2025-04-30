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
