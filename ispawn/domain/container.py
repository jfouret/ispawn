from enum import Enum
from typing import List, Dict, Union, Optional
from pathlib import Path
import os

class Service(str, Enum):
    """Available services that can be run in containers."""
    JUPYTER = "jupyter"
    RSTUDIO = "rstudio"
    VSCODE = "vscode"

    @classmethod
    def from_str(cls, value: str) -> "Service":
        """
        Create Service from string.
        
        Args:
            value (str): Service name to convert
        
        Returns:
            Service: Corresponding Service enum value
        
        Raises:
            ValueError: If the service name is invalid
        """
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid service: {value}")

class ContainerConfig:
    """
    Configuration for a container with comprehensive settings.
    
    Attributes:
        raw_name (str): Original container name
        container_name (str): Fully qualified container name with prefix
        network_name (str): Docker network name
        image (str): Docker image to use
        services (List[Service]): List of services to run in the container
        username (str): Username for services
        password (str): Password for services
        uid (int): User ID to run services as
        gid (int): Group ID to run services as
        domain (str): Domain for service URLs
        dns (List[str]): List of DNS servers
        volumes (List[str]): List of volume mount configurations
        host_prefix (str): Prefix to add to volumes mounted from the host
        log_dir (Path): Directory for container logs
        cert_mode (str): Certificate mode ('provided' or 'letsencrypt')
    """

    def __init__(
        self,
        name: str,
        ispawn_prefix: str,
        network_name: str,
        image: str,
        services: Union[List[Service], List[str]],
        username: str,
        password: str,
        uid: int,
        gid: int,
        domain: str,
        dns: Optional[List[str]] = None,
        volumes: Optional[List[str]] = None,
        host_prefix: str = "/mnt/host",
        log_base_dir: Optional[Union[str, Path]] = None,
        cert_mode: str = "provided"
    ):
        """
        Initialize container configuration.
        
        Args:
            name (str): Container name
            ispawn_prefix (str): Prefix for container naming
            network_name (str): Docker network name
            image (str): Docker image to use
            services (List[Service] or List[str]): Services to run
            username (str): Username for services
            password (str): Password for services
            uid (int): User ID to run services
            gid (int): Group ID to run services
            domain (str): Domain for service URLs
            dns (Optional[List[str]], optional): DNS servers. Defaults to Google DNS.
            volumes (Optional[List[str]], optional): Volume mounts
            host_prefix (str, optional): Prefix for host volumes. Defaults to "/mnt/host".
            log_base_dir (Optional[Union[str, Path]], optional): Base log directory
            cert_mode (str, optional): Certificate mode. Defaults to "provided".
        
        Raises:
            ValueError: If cert_mode is invalid
        """
        # Validate inputs
        if cert_mode not in ["provided", "letsencrypt"]:
            raise ValueError("cert_mode must be 'provided' or 'letsencrypt'")

        self.raw_name = name
        self.container_name = f"{ispawn_prefix}-{name}"
        self.network_name = network_name
        self.image = image
        
        # Convert services to Service enum if needed
        self.services = [
            Service.from_str(s) if isinstance(s, str) else s 
            for s in services
        ]
        
        self.username = username
        self.password = password
        self.uid = uid
        self.gid = gid
        self.domain = domain
        
        # Default DNS if not provided
        self.dns = dns or ["8.8.8.8", "8.8.4.4"]
        self.cert_mode = cert_mode
        self.host_prefix = host_prefix
        
        # Process volumes
        self._raw_volumes = volumes or [str(Path.home())]
        self.volumes = [
            f"{volume}:{os.path.join(self.host_prefix, volume.lstrip('/'))}"
            for volume in self._raw_volumes
        ]
        
        # Setup log directory
        if log_base_dir:
            log_base_path = Path(log_base_dir) / name
            self.log_dir = self._setup_log_dir(log_base_path)
            self.volumes.append(f"{self.log_dir}:/var/log/ispawn:rw")
        else:
            self.log_dir = None

    def _setup_log_dir(self, base_path: Path) -> Path:
        """
        Setup log directory with automatic numbering.
        
        Args:
            base_path (Path): Base path for log directory
        
        Returns:
            Path: Path to the unique log directory
        """
        counter = 1
        while True:
            log_dir = base_path.with_name(f"{base_path.name}.{counter}")
            if not log_dir.exists():
                log_dir.mkdir(parents=True, exist_ok=True)
                return log_dir
            counter += 1

    def get_labels(self) -> List[str]:
        """
        Generate container labels for Traefik routing and service identification.
        
        Returns:
            List[str]: List of Docker labels
        """
        labels = [
            f"ispawn.container={self.raw_name}",
            f"ispawn.domain={self.domain}",
            "traefik.enable=true",
            "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https",
            "traefik.http.middlewares.redirect-to-https.redirectscheme.permanent=true"
        ]
        
        # Service-specific labels
        service_configs = {
            Service.JUPYTER: {"port": 8888, "prefix": "jupyter"},
            Service.RSTUDIO: {"port": 8787, "prefix": "rstudio"},
            Service.VSCODE: {"port": 8842, "prefix": "vscode"}
        }
        
        for service in self.services:
            config = service_configs.get(service)
            if config:
                service_labels = [
                    f"ispawn.service.{config['prefix']}=true",
                    f"ispawn.port.{config['prefix']}={config['port']}",
                    f"traefik.http.routers.{config['prefix']}-{self.raw_name}.rule=Host(`{config['prefix']}-{self.raw_name}.{self.domain}`)",
                    f"traefik.http.routers.{config['prefix']}-{self.raw_name}.entrypoints=websecure",
                    f"traefik.http.services.{config['prefix']}-{self.raw_name}.loadbalancer.server.port={config['port']}",
                    f"traefik.http.routers.{config['prefix']}-{self.raw_name}.middlewares=redirect-to-https"
                ]
                
                # TLS configuration
                tls_label = (
                    f"traefik.http.routers.{config['prefix']}-{self.raw_name}.tls.certresolver=letsencrypt"
                    if self.cert_mode == "letsencrypt" 
                    else f"traefik.http.routers.{config['prefix']}-{self.raw_name}.tls=true"
                )
                service_labels.append(tls_label)
                
                labels.extend(service_labels)
        
        return labels

    def get_environment(self) -> Dict[str, str]:
        """
        Generate environment variables for the container.
        
        Returns:
            Dict[str, str]: Dictionary of environment variables
        """
        return {
            "USERNAME": self.username,
            "PASSWORD": self.password,
            "UID": str(self.uid),
            "GID": str(self.gid),
            "SERVICES": ",".join(s.value for s in self.services)
        }

    def get_volume_mounts(self) -> List[str]:
        """
        Get container volume mount configurations.
        
        Returns:
            List[str]: List of volume mount configurations
        """
        return self.volumes

    def get_service_urls(self) -> Dict[Service, str]:
        """
        Generate service access URLs.
        
        Returns:
            Dict[Service, str]: Dictionary of service URLs
        """
        urls = {}
        for service in self.services:
            if service == Service.JUPYTER:
                urls[service] = f"https://jupyter-{self.raw_name}.{self.domain}?token={self.password}"
            elif service == Service.RSTUDIO:
                urls[service] = f"https://rstudio-{self.raw_name}.{self.domain}"
            elif service == Service.VSCODE:
                urls[service] = f"https://vscode-{self.raw_name}.{self.domain}"
        return urls
