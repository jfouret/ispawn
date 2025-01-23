import docker
from typing import List, Dict, Optional
from pathlib import Path
from docker.models.containers import Container as DockerContainer
from docker.models.networks import Network
from docker.types import Mount
from ispawn.domain.container import ContainerConfig
from ispawn.domain.config import Config
from ispawn.domain.exceptions import ContainerError, NetworkError, ImageError
import re

class ContainerService:
    """Service for handling Docker operations."""

    def __init__(self, config: Config):
        """Initialize the Docker client."""
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            raise ContainerError(f"Failed to initialize Docker client: {str(e)}")
        self.config = config
    def run_container(self, config: ContainerConfig, force: bool = False) -> DockerContainer:
        """Run a Docker container with the specified configuration.
        
        Args:
            container: Container configuration
            force: Whether to force replace an existing container
            
        Returns:
            Running Docker container
            
        Raises:
            ContainerError: If container operations fail
        """
        try:
            # Check if container already exists
            existing = self.get_container(config.container_name)
            if existing:
                if not force:
                    raise ContainerError(f"Container {config.container_name} already exists")
                self.remove_container(config.container_name)

            # Parse volume mounts
            mounts = []
            for volume in config.volumes:
                src, dst = volume[:2]
                if len(volume) == 3:
                    mode = volume[2]
                else:
                    mode = "rw"
                mounts.append(
                    Mount(
                        target = dst,
                        source = src,
                        type = "bind",
                        read_only = (mode == "ro")
                    )
                )

            # Prepare container configuration
            container_config = {
                "name": config.container_name,
                "image": config.image_config.target_image,
                "detach": True,
                "environment": config.environment(),
                "labels": config.get_labels(),
                "network": config.config.network_name,
                "mounts": mounts,
                "command": "sleep infinity"
            }


            # Run the container
            return self.client.containers.run(**container_config)
        except docker.errors.ImageNotFound:
            raise ImageError(f"Image {config.image_config.target_image} not found")
        except docker.errors.APIError as e:
            raise ContainerError(f"Failed to run container {config.container_name}: {str(e)}")

    def remove_container(self, name: str, force: bool = True) -> None:
        """Remove a Docker container."""
        container = self.get_container(name)
        if container:
            try:
                container.remove(force=force)
            except docker.errors.APIError as e:
                raise ContainerError(f"Failed to remove container {name}: {str(e)}")

    def list_containers(self) -> List[Dict[str, str]]:
        """List all ispawn containers.
        
        Returns:
            List[Dict[str, str]]: List of container information
            
        Raises:
            ContainerError: If container listing fails
        """
        try:
            containers = self.client.containers.list(all=True)
            result = []
            for c in containers:
                if not c.name.startswith(self.config.container_name_prefix):
                    continue
                    
                # Handle containers with no tags
                image_name = c.image.tags[0] if c.image.tags else "none:latest"
                
                # Get service URLs from Traefik labels
                service_urls = []
                
                for label, value in c.labels.items():
                    # Match router rule labels
                    router_match = re.match(r'traefik\.http\.routers\.([^.]+)\.rule', label)
                    if router_match:
                        service_id = router_match.group(1)
                        service_match = re.match(f'([^-]+)-{c.name}$', service_id)
                        if service_match:
                            domain_match = re.search(r'Host\(`([^`]+)`\)', value)
                            if domain_match:
                                domain = domain_match.group(1)
                                service_urls.append(f"https://{domain}")
                
                result.append({
                    "name": c.name,
                    "urls": service_urls,
                    "image": image_name,
                    "status": c.status,
                    "id": c.short_id
                })
            return result
        except docker.errors.APIError as e:
            raise ContainerError(f"Failed to list containers: {str(e)}")

    def get_container(self, name: str) -> Optional[DockerContainer]:
        """Get a Docker container by name.
        
        Args:
            name: Container name
            
        Returns:
            Optional[DockerContainer]: Container if found, None otherwise
            
        Raises:
            ContainerError: If container operations fail
        """
        try:
            containers = self.client.containers.list(all=True, filters={"name": f"^{name}$"})
            return containers[0] if containers else None
        except docker.errors.APIError as e:
            raise ContainerError(f"Failed to get container {name}: {str(e)}")

    def get_image(self, name: str) -> bool:
        """Check if a Docker image exists."""
        try:
            self.client.images.get(name)
            return True
        except docker.errors.ImageNotFound:
            return False
        except docker.errors.APIError as e:
            raise ImageError(f"Failed to check image {name}: {str(e)}")
