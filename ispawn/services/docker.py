import docker
from typing import List, Dict, Optional
from pathlib import Path
from docker.models.containers import Container as DockerContainer
from docker.models.networks import Network
from ispawn.domain.container import ContainerConfig, Service
from ispawn.domain.proxy import ProxyConfig
from ispawn.domain.exceptions import ContainerError, NetworkError, ImageError

class DockerService:
    """Service for handling Docker operations."""

    def __init__(self):
        """Initialize the Docker client."""
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            raise ContainerError(f"Failed to initialize Docker client: {str(e)}")

    def create_network(self, config: ProxyConfig) -> Network:
        """Create a Docker network for ispawn containers.
        
        Args:
            config: Proxy configuration containing network settings
            
        Returns:
            Created Docker network
            
        Raises:
            NetworkError: If network creation fails
        """
        try:
            return self.client.networks.create(
                config.network_name,
                driver="bridge",
                ipam=docker.types.IPAMConfig(
                    pool_configs=[docker.types.IPAMPool(subnet=config.subnet)]
                ),
                labels={"created_by": "ispawn"}
            )
        except docker.errors.APIError as e:
            raise NetworkError(f"Failed to create network {config.network_name}: {str(e)}")

    def get_network(self, name: str) -> Optional[Network]:
        """Get a Docker network by name."""
        try:
            networks = self.client.networks.list(filters={"name": name})
            return networks[0] if networks else None
        except docker.errors.APIError as e:
            raise NetworkError(f"Failed to get network {name}: {str(e)}")

    def ensure_network(self, config: ProxyConfig) -> Network:
        """Ensure a Docker network exists, creating it if necessary.
        
        Args:
            config: Proxy configuration containing network settings
            
        Returns:
            Existing or newly created Docker network
            
        Raises:
            NetworkError: If network operations fail
        """
        network = self.get_network(config.network_name)
        if not network:
            network = self.create_network(config)
        return network

    def run_container(self, config: ContainerConfig, force: bool = False, command: Optional[str] = None) -> DockerContainer:
        """Run a Docker container with the specified configuration.
        
        Args:
            container: Container configuration
            force: Force replace existing container if it exists
            command: Optional command to run in the container
            
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
            volumes = {}
            for mount in config.get_volume_mounts():
                parts = mount.split(":")
                if len(parts) >= 2:
                    src = parts[0]
                    dst = parts[1]
                    mode = parts[2] if len(parts) > 2 else "rw"
                    volumes[str(src)] = {"bind": str(dst), "mode": mode}

            # Prepare container configuration
            container_config = {
                "name": config.container_name,
                "image": config.image,
                "detach": True,
                "environment": config.get_environment(),
                "labels": {label: "true" for label in config.get_labels()},
                "network": config.network_name,
                "volumes": volumes
            }

            # Add command if provided
            if command:
                container_config["command"] = command

            # Run the container
            return self.client.containers.run(**container_config)
        except docker.errors.ImageNotFound:
            raise ImageError(f"Image {config.image} not found")
        except docker.errors.APIError as e:
            raise ContainerError(f"Failed to run container {config.container_name}: {str(e)}")

    def get_container(self, name: str) -> Optional[DockerContainer]:
        """Get a Docker container by name."""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"name": name}
            )
            return containers[0] if containers else None
        except docker.errors.APIError as e:
            raise ContainerError(f"Failed to get container {name}: {str(e)}")

    def remove_container(self, name: str, force: bool = True) -> None:
        """Remove a Docker container."""
        container = self.get_container(name)
        if container:
            try:
                container.remove(force=force)
            except docker.errors.APIError as e:
                raise ContainerError(f"Failed to remove container {name}: {str(e)}")

    def list_containers(self, prefix: str = "ispawn-") -> List[Dict[str, str]]:
        """List all ispawn containers."""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"name": prefix}
            )
            result = []
            for c in containers:
                try:
                    image_name = c.image.tags[0] if c.image.tags else "none"
                except docker.errors.ImageNotFound:
                    image_name = "none"
                
                result.append({
                    "name": c.name,
                    "image": image_name,
                    "status": c.status,
                    "id": c.short_id
                })
            return result
        except docker.errors.APIError as e:
            raise ContainerError(f"Failed to list containers: {str(e)}")

    def get_image(self, name: str) -> bool:
        """Check if a Docker image exists."""
        try:
            self.client.images.get(name)
            return True
        except docker.errors.ImageNotFound:
            return False
        except docker.errors.APIError as e:
            raise ImageError(f"Failed to check image {name}: {str(e)}")
