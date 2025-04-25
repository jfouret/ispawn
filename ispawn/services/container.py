import docker
from typing import List, Dict
from docker.models.containers import Container
from docker.types import Mount
from ispawn.domain.container import ContainerConfig
from ispawn.domain.config import Config
from ispawn.domain.exceptions import ContainerError
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
    def run_container(self, config: ContainerConfig, force: bool = False) -> Container:
        """Run a Docker container with the specified configuration.
        
        Args:
            container: Container configuration
            force: Whether to force replace an existing container
            
        Returns:
            Running Docker container
            
        Raises:
            ContainerError: If container operations fail
        """
        # Check if container already exists
        try:
            existing = self.client.containers.get(config.container_name)
        except:
            existing = False
        if existing:
            if force:
                self.remove_container(config.container_name, force = True)
            else:
                raise ContainerError(f"Container {config.container_name} already exists")

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
        containers = self.client.containers.list(all=True)
        result = []
        for c in containers:
            if not c.name.startswith(self.config.container_name_prefix):
                continue
            if c.name.endswith("-traefik"):
                continue
            try:
                image_name = c.image.tags[0]
            except:
                image_name = c.attrs["Image"].split(":")[-1][:12]
            
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

    def stop_container(self, container_id: str) -> None:
        container: Container = self.client.containers.get(container_id)
        container.stop()

    def remove_container(self, container_id: str, force: bool = False) -> None:
        container: Container = self.client.containers.get(container_id)
        container.remove(force = force)