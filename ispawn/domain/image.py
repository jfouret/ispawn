from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
from ispawn.domain.container import Service

@dataclass
class ImageConfig:
    """Configuration for building a Docker image."""
    base_image: str
    services: List[Service]
    name_prefix: str = "ispawn"
    env_file: Optional[Path] = None
    setup_file: Optional[Path] = None

    def __post_init__(self):
        """Validate and process configuration after initialization."""
        # Convert string services to enum if needed
        if isinstance(self.services[0], str):
            self.services = [Service(s) for s in self.services]

    @property
    def target_image(self) -> str:
        """Get the target image name."""
        # Convert base image name to target image name
        # e.g., ubuntu:20.04 -> ispawn-ubuntu:20.04
        base_name, tag = self.base_image.split(':')
        base_name = base_name.split('/')[-1]  # Handle registry paths
        return f"{self.name_prefix}-{base_name}:{tag}"

    def get_build_args(self) -> Dict[str, str]:
        """Get build arguments for the Dockerfile."""
        return {
            "BASE_IMAGE": self.base_image,
            "SERVICES": ",".join(s.value for s in self.services)
        }

class ImageBuilder:
    """Handles Docker image building operations."""

    def __init__(self, config: ImageConfig):
        """Initialize image builder.
        
        Args:
            config: Image configuration
        """
        self.config = config
        self.templates_dir = Path(__file__).parent.parent / "templates"

    def get_dockerfile_path(self) -> Path:
        """Get path to the Dockerfile template."""
        return self.templates_dir / "Dockerfile.j2"

    def get_entrypoint_path(self) -> Path:
        """Get path to the entrypoint script template."""
        return self.templates_dir / "entrypoint.sh.j2"

    def get_context_files(self) -> Dict[str, Path]:
        """Get files needed for the build context."""
        context = {}
        
        # Add optional files if they exist
        if self.config.env_file and self.config.env_file.exists():
            context["environment"] = self.config.env_file
        if self.config.setup_file and self.config.setup_file.exists():
            context["setup"] = self.config.setup_file

        return context

    def get_build_args(self) -> Dict[str, str]:
        """Get build arguments for the Dockerfile."""
        return self.config.get_build_args()

    def get_build_context(self) -> Dict[str, Any]:
        """Get the complete build context for the image."""
        return {
            "dockerfile": self.get_dockerfile_path(),
            "entrypoint": self.get_entrypoint_path(),
            "context_files": self.get_context_files(),
            "build_args": self.get_build_args(),
            "target_image": self.config.target_image
        }
