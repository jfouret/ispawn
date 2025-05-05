from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from importlib import import_module
from ispawn.domain.config import Config

# Get available services from directory structure
SERVICES = {
    d.name.upper(): d.name
    for d in (Path(__file__).parent / "services").iterdir()
    if d.is_dir()
}

# Create the Enum as before
Service = Enum("Service", SERVICES)


# Add property to access config
def port(self) -> Optional[int]:
    """Get the port number defined in the service's config."""
    try:
        config = import_module(f"ispawn.domain.services.{self.value}.config")
        return getattr(config, "PORT", None)
    except ImportError:
        return None


def volumes(self) -> Dict[str, str]:
    """Get the volume mappings defined in the service's config.

    Returns:
        Dict[str, str]: Dictionary mapping host directory names to container
            paths
    """
    try:
        config = import_module(f"ispawn.domain.services.{self.value}.config")
        return getattr(config, "VOLUMES", {})
    except ImportError:
        return {}


# Add the properties to the Enum
Service.port = property(port)
Service.volumes = property(volumes)


@classmethod
def from_str(cls: Service, s: str) -> Service:
    try:
        return cls(s)
    except ValueError:
        raise ValueError(f"No matching service found for '{s}'")


Service.from_str = from_str


class ImageConfig:
    """
    Configuration for building a Docker image with comprehensive settings.

    Attributes:
        base (str): Base Docker image to build from
        services (List[str]): List of services to include in the image
        config (Config): Configuration object containing build settings
    """

    def __init__(self, config: Config, base: str, services: List[str]):
        """
        Initialize image configuration.

        Args:
            config (Config): Configuration object containing build settings
            base (str): Base Docker image to build from
            services (List[Service]): Services to include in the image
        """
        self.base = base
        # Convert string services to enum if needed
        self.services = [Service.from_str(s) for s in services]
        self.config = config

        # Get chunk paths from config
        self.env_chunk_path = (
            Path(config.env_chunk_path) if config.env_chunk_path else None
        )
        self.dockerfile_chunk_path = (
            Path(config.dockerfile_chunk_path)
            if config.dockerfile_chunk_path
            else None
        )
        self.entrypoint_chunk_path = (
            Path(config.entrypoint_chunk_path)
            if config.entrypoint_chunk_path
            else None
        )

        # Validate paths if they exist
        for path in [
            "env_chunk_path",
            "dockerfile_chunk_path",
            "entrypoint_chunk_path",
        ]:
            v_path = self.__getattribute__(path)
            if v_path is not None:
                if not v_path.exists():
                    raise FileNotFoundError(f"File not found: {v_path}")

        self.templates_dir = Path(__file__).parent.parent / "templates"

    @property
    def target_image(self) -> str:
        """
        Get the target image name.

        Returns:
            str: Target image name with prefix and tag
        """
        services = [s.value for s in self.services]
        services.sort()
        services = "-".join(services)
        if ":" in self.base:
            base_name, tag = self.base.split(":")
            return (
                f"{self.config.image_name_prefix}{base_name}:{tag}-{services}"
            )
        else:
            return f"{self.config.image_name_prefix}{self.base}:{services}"

    @property
    def dockerfile_template_path(self) -> Path:
        """
        Get path to the Dockerfile template.

        Returns:
            Path: Path to Dockerfile template
        """
        return self.templates_dir / "Dockerfile.j2"

    @property
    def entrypoint_template_path(self) -> Path:
        """
        Get path to the entrypoint script template.

        Returns:
            Path: Path to entrypoint script template
        """
        return self.templates_dir / "entrypoint.sh.j2"

    def _load_dockerfile_chunks(self, chunk_type: str) -> List[str]:
        """
        Load chunks of specified type for each service.

        Args:
            chunk_type: Type of chunk to load ('Dockerfile' or 'entrypoint.sh')

        Returns:
            List[str]: List of chunks
        """
        chunks = []
        for service in self.services:
            chunk_path = (
                Path(__file__).parent
                / "services"
                / service.value
                / "Dockerfile"
            )
            if chunk_path.exists():
                # Read content and normalize line endings
                content = chunk_path.read_text()
                content = content.replace("\r\n", "\n").strip()
                chunks.append(content)
            else:
                raise FileNotFoundError(
                    (
                        "Dockerfile chunk not found for service:"
                        f"{service.value} ({chunk_path})"
                    )
                )
        return "\n\n".join(chunks) + "\n"

    def get_template_context(self, template_type: str) -> Dict[str, Any]:
        """
        Get template context for specified template type.

        Args:
            template_type: Type of template ('Dockerfile' or 'entrypoint.sh')

        Returns:
            Dict[str, Any]: Template context variables
        """
        context = {"services": [s.value for s in self.services]}

        # Add template-specific variables
        if template_type == "Dockerfile":
            context = {
                **context,
                "service_chunks": self._load_dockerfile_chunks(template_type),
                "has_env_in_context": True if self.env_chunk_path else False,
                "dockerfile_chunk": self.dockerfile_chunk_path.read_text()
                if self.dockerfile_chunk_path
                else "",
                "base": self.base,
            }
        if template_type == "entrypoint.sh":
            context = {
                **context,
                "entrypoint_chunk": self.entrypoint_chunk_path.read_text()
                if self.entrypoint_chunk_path
                else "",
                "timezone": self.config.timezone,
            }

        return context

    def get_dockerfile_args(self) -> Dict[str, str]:
        """Get Dockerfile template context."""
        return self.get_template_context("Dockerfile")

    def get_entrypoint_args(self) -> Dict[str, str]:
        """Get entrypoint template context."""
        return self.get_template_context("entrypoint.sh")

    def get_build_context(self) -> Dict[str, Any]:
        """
        Get the complete build context for the image.

        Returns:
            Dict[str, Any]: Complete build context including all necessary
                files and arguments
        """
        context = {
            "Dockerfile": {
                "template": self.dockerfile_template_path,
                "args": self.get_dockerfile_args(),
            },
            "entrypoint.sh": {
                "template": self.entrypoint_template_path,
                "args": self.get_entrypoint_args(),
            },
        }
        if self.env_chunk_path:
            context["environment"] = {"file": self.env_chunk_path.resolve()}
        for service in self.services:
            context[f"ispawn-entrypoint-{service.value}.sh"] = {
                "file": Path(__file__).parent
                / "services"
                / service.value
                / "entrypoint.sh"
            }
        return context
