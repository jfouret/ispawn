import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import jinja2
import docker
from docker.models.images import Image

from ispawn.domain.image import ImageBuilder, ImageConfig
from ispawn.domain.exceptions import ImageError

class ImageService:
    """Service for handling Docker image operations."""

    def __init__(self):
        """Initialize the Docker client."""
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            raise ImageError(f"Failed to initialize Docker client: {str(e)}")

    def build_image(self, builder: ImageBuilder) -> Image:
        """Build a Docker image using the provided builder.
        
        Args:
            builder: ImageBuilder instance with build configuration
            
        Returns:
            Built Docker image
            
        Raises:
            ImageError: If image build fails
        """
        try:
            # Get build context
            context = builder.get_build_context()
            
            # Create temporary build directory
            with tempfile.TemporaryDirectory() as build_dir:
                build_path = Path(build_dir)
                
                # Render Dockerfile from template
                dockerfile_content = self._render_template(
                    context["dockerfile"],
                    context["build_args"]
                )
                dockerfile_path = build_path / "Dockerfile"
                dockerfile_path.write_text(dockerfile_content)
                
                # Render entrypoint script from template
                entrypoint_content = self._render_template(
                    context["entrypoint"],
                    context["build_args"]
                )
                entrypoint_path = build_path / "entrypoint.sh"
                entrypoint_path.write_text(entrypoint_content)
                os.chmod(entrypoint_path, 0o755)  # Make executable
                
                # Copy context files
                for name, path in context["context_files"].items():
                    shutil.copy2(path, build_path / name)
                
                # Build image
                image, _ = self.client.images.build(
                    path=str(build_path),
                    tag=context["target_image"],
                    buildargs=context["build_args"],
                    rm=True  # Remove intermediate containers
                )
                
                return image

        except (docker.errors.BuildError, docker.errors.APIError) as e:
            raise ImageError(f"Failed to build image: {str(e)}")
        except Exception as e:
            raise ImageError(f"Unexpected error during build: {str(e)}")

    def _render_template(self, template_path: Path, context: Dict[str, Any]) -> str:
        """Render a Jinja2 template.
        
        Args:
            template_path: Path to template file
            context: Template context variables
            
        Returns:
            Rendered template content
            
        Raises:
            ImageError: If template rendering fails
        """
        try:
            with open(template_path, 'r') as f:
                template = jinja2.Template(f.read())
            return template.render(**context)
        except Exception as e:
            raise ImageError(f"Failed to render template {template_path}: {str(e)}")

    def list_images(self, prefix: str = "ispawn-") -> List[Dict[str, str]]:
        """List all ispawn images.
        
        Args:
            prefix: Image name prefix to filter by
            
        Returns:
            List of image information dictionaries
            
        Raises:
            ImageError: If listing images fails
        """
        try:
            images = self.client.images.list(
                filters={"reference": f"{prefix}*"}
            )
            return [
                {
                    "id": image.short_id,
                    "tags": image.tags,
                    "size": self._format_size(image.attrs["Size"]),
                    "created": image.attrs["Created"]
                }
                for image in images
            ]
        except docker.errors.APIError as e:
            raise ImageError(f"Failed to list images: {str(e)}")

    def remove_image(self, name: str, force: bool = False) -> None:
        """Remove a Docker image.
        
        Args:
            name: Name of the image to remove
            force: Force removal of the image
            
        Raises:
            ImageError: If image removal fails
        """
        try:
            self.client.images.remove(name, force=force)
        except docker.errors.ImageNotFound:
            raise ImageError(f"Image not found: {name}")
        except docker.errors.APIError as e:
            raise ImageError(f"Failed to remove image {name}: {str(e)}")

    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable string.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string (e.g., "1.2 GB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
