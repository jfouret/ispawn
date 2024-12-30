from pathlib import Path
from typing import Dict, List, Optional, Any
from ispawn.domain.container import Service

class ImageConfig:
    """
    Configuration for building a Docker image with comprehensive settings.
    
    Attributes:
        base_image (str): Base Docker image to build from
        services (List[Service]): List of services to include in the image
        name_prefix (str): Prefix for the target image name
        env_file (Optional[Path]): Path to environment file to include
        setup_file (Optional[Path]): Path to setup script to include
        templates_dir (Path): Directory containing template files
    """

    def __init__(
        self,
        base_image: str,
        services: List[Service],
        name_prefix: str,
        env_file: Optional[Path],
        setup_file: Optional[Path],
        templates_dir: Optional[Path] = None
    ):
        """
        Initialize image configuration.
        
        Args:
            base_image (str): Base Docker image to build from
            services (List[Service]): Services to include in the image
            name_prefix (str): Prefix for the target image name
            env_file (Optional[Path]): Path to environment file
            setup_file (Optional[Path]): Path to setup script
            templates_dir (Optional[Path]): Directory containing templates
        """
        self.base_image = base_image
        # Convert string services to enum if needed
        self.services = [
            Service.from_str(s) if isinstance(s, str) else s 
            for s in services
        ]
        self.name_prefix = name_prefix
        self.env_file = env_file
        self.setup_file = setup_file
        self.templates_dir = templates_dir or Path(__file__).parent.parent / "templates"

    @property
    def target_image(self) -> str:
        """
        Get the target image name.
        
        Returns:
            str: Target image name with prefix and tag
        """
        base_name, tag = self.base_image.split(':')
        base_name = base_name.split('/')[-1]  # Handle registry paths
        return f"{self.name_prefix}-{base_name}:{tag}"

    @property
    def dockerfile_path(self) -> Path:
        """
        Get path to the Dockerfile template.
        
        Returns:
            Path: Path to Dockerfile template
        """
        return self.templates_dir / "Dockerfile.j2"

    @property
    def entrypoint_path(self) -> Path:
        """
        Get path to the entrypoint script template.
        
        Returns:
            Path: Path to entrypoint script template
        """
        return self.templates_dir / "entrypoint.sh.j2"

    def get_build_args(self) -> Dict[str, str]:
        """
        Get build arguments for the Dockerfile.
        
        Returns:
            Dict[str, str]: Dictionary of build arguments
        """
        return {
            "BASE_IMAGE": self.base_image,
            "SERVICES": ",".join(s.value for s in self.services)
        }

    def get_context_files(self) -> Dict[str, Path]:
        """
        Get files needed for the build context.
        
        Returns:
            Dict[str, Path]: Dictionary of context files
        """
        context = {}
        
        # Add optional files if they exist
        if self.env_file and self.env_file.exists():
            context["environment"] = self.env_file
        if self.setup_file and self.setup_file.exists():
            context["setup"] = self.setup_file

        return context

    def get_build_context(self) -> Dict[str, Any]:
        """
        Get the complete build context for the image.
        
        Returns:
            Dict[str, Any]: Complete build context including all necessary files and arguments
        """
        return {
            "dockerfile": self.dockerfile_path,
            "entrypoint": self.entrypoint_path,
            "context_files": self.get_context_files(),
            "build_args": self.get_build_args(),
            "target_image": self.target_image
        }
