import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import jinja2
import docker
from docker.models.images import Image

from ispawn.domain.image import ImageConfig
from ispawn.domain.exceptions import ImageError
from ispawn.domain.config import Config


class ImageService:
    """Service for handling Docker image operations."""

    def __init__(self, config: Config):
        """Initialize the Docker client."""
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            raise ImageError(f"Failed to initialize Docker client: {str(e)}")
        self.config = config

    def check_image(self, config: ImageConfig) -> bool:
        """Check if a Docker image exists based on the provided configuration."""
        try:
            self.client.images.get(config.target_image)
            return True
        except:
            return False

    def build_image(self, config: ImageConfig) -> Image:
        """Build a Docker image using the provided configuration.

        Args:
            config: ImageConfig instance with build configuration

        Returns:
            Built Docker image

        Raises:
            ImageError: If image build fails
        """
        # Get build context
        context = config.get_build_context()

        # Create temporary build directory
        build_dir = tempfile.mkdtemp()
        build_path = Path(build_dir)

        try:
            for context_id, context_dict in context.items():
                file_path = build_path / context_id
                if "file" in context_dict.keys():
                    shutil.copy2(context_dict["file"], file_path)
                elif "template" in context_dict.keys():
                    context_content = self._render_template(
                        context_dict["template"], context_dict["args"]
                    )
                    file_path.write_text(context_content)
                else:
                    raise ImageError(f"Invalid build context: {context_id}")
            # Build image
            try:
                image, _ = self.client.images.build(
                    path=str(build_path),
                    tag=config.target_image,
                    rm=True,
                    quiet=False,
                )
            except docker.errors.BuildError as e:
                print(f"Build dir in {build_path}")
                print("=================")
                # Print the build logs from the error
                for log in e.build_log:
                    if "stream" in log:
                        print(log["stream"].strip())
                    if "error" in log:
                        print(f"ERROR: {log['error'].strip()}")
                    if "errorDetail" in log:
                        print(
                            f"Error Detail: {log['errorDetail'].get('message', '').strip()}"
                        )
                sys.exit(1)
            except docker.errors.APIError as e:
                print(f"Docker API error: {str(e)}")
                sys.exit(1)
            except Exception as e:
                raise ImageError(f"Unexpected error: {str(e)}") from e

            # Clean up build directory only on success
            shutil.rmtree(build_dir)
            return image
        except Exception as e:
            # Keep build directory in case of error and include path in error message
            error_msg = (
                f"Build failed (build files preserved in {build_dir}): {str(e)}"
            )
            if isinstance(
                e,
                (docker.errors.BuildError, docker.errors.APIError, ImageError),
            ):
                raise ImageError(error_msg) from e
            raise ImageError(f"{error_msg} (unexpected error)")

    def _render_template(
        self, template_path: Path, context: Dict[str, Any]
    ) -> str:
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
            with open(template_path, "r") as f:
                template = jinja2.Template(f.read())
            return template.render(**context)
        except Exception as e:
            raise ImageError(
                f"Failed to render template {template_path}: {str(e)}"
            )

    def list_images(self) -> List[Dict[str, str]]:
        """List all ispawn images.

        Args:
            prefix: Image name prefix to filter by

        Returns:
            List of image information dictionaries

        Raises:
            ImageError: If listing images fails
        """
        try:
            # Get all images and filter manually since Docker's filter doesn't work reliably
            images = self.client.images.list()
            # Filter images by prefix
            filtered_images = []
            for img in images:
                # Only include images that have exactly one tag and it starts with our prefix
                if any(
                    tag.startswith(f"{self.config.image_name_prefix}")
                    for tag in img.tags
                ):
                    filtered_images.append(img)
            images = filtered_images
            return [
                {
                    "id": image.short_id[7:],
                    "tags": image.tags,
                    "size": self._format_size(image.attrs["Size"]),
                    "created": image.attrs["Created"],
                }
                for image in images
            ]
        except docker.errors.APIError as e:
            raise ImageError(f"Failed to list images: {str(e)}")

    def remove_image(self, digest: str, force: bool = False) -> None:
        """Remove a Docker image.

        Args:
            name: Name of the image to remove
            force: Force removal of the image

        Raises:
            ImageError: If image removal fails
        """
        try:
            self.client.images.remove(digest, force=force)
        except docker.errors.ImageNotFound:
            raise ImageError(f"Image not found: {digest}")
        except docker.errors.APIError as e:
            raise ImageError(f"Failed to remove image {digest}: {str(e)}")

    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string (e.g., "1.2 GB")
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
