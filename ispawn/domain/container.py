from typing import List, Dict, Union, Optional
from pathlib import Path
import os
import getpass

from ispawn.domain.image import Service, ImageConfig
from ispawn.domain.config import Config

class ContainerConfig:
    """
    Configuration for a container with comprehensive settings.
    
    Attributes:
        name (str): Original container name
        group (str): Required group for RStudio access (defaults to username)
    """

    def __init__(
        self,
        name: str,
        config: Config,
        image_config: ImageConfig,
        volumes: List[List[str]],
        group: Optional[str] = None
    ):
        """
        Initialize container configuration.
        
        Args:
            name: Container name
            config: Global configuration
            image_config: Image configuration
            volumes: List of volume mappings
            group: Required group for RStudio access (defaults to username)
        
        Raises:
            ValueError: If cert_mode is invalid
        """

        self.config = config
        self.raw_name = name
        self.container_name = f"{config.container_name_prefix}{name}"
        self.image_config = image_config
        self.group = group or getpass.getuser()
        
        # Create log and volume directories
        log_dir = Path(config.user_root_dir) / self.container_name / "logs"
        vol_dir = Path(config.user_root_dir) / self.container_name / "volumes"
        log_dir.mkdir(parents=True, exist_ok=True)
        vol_dir.mkdir(parents=True, exist_ok=True)
        self.vol_dir = str(vol_dir)
        self.log_dir = str(log_dir)
        
        # Process volumes
        self.volumes = config.volumes.copy()
        self.volumes.extend(volumes)
        self.volumes.append([f"{self.log_dir}", "/var/log/ispawn"])
        
        # Add service-specific volumes last
        for service in self.image_config.services:
            service_volumes = service.volumes
            for host_dir, container_path in service_volumes.items():
                # Create service-specific directory
                service_vol_dir = Path(self.vol_dir) / service.value / host_dir
                service_vol_dir.mkdir(parents=True, exist_ok=True)
                # Add volume mapping
                username = getpass.getuser()
                self.volumes.append([str(service_vol_dir), container_path.replace("~", f"/home/{username}")])

    def get_labels(self) -> Dict[str, str]:
        """
        Generate container labels for Traefik routing and service identification.
        
        Returns:
            Dict[str, str]: Dictionary of Docker labels
        """
        labels = {
            "traefik.enable": "true",
            "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme": "https",
            "traefik.http.middlewares.redirect-to-https.redirectscheme.permanent": "true"
        }
        
        for service in self.image_config.services:
            service_domain = self.get_service_domain(service)
            router_id = f"{self.container_name}-{service.value}"
            service_id = f"{self.container_name}-{service.value}-service"
            
            labels.update({
                f"ispawn.port.{service.value}": str(service.port),
                f"traefik.http.routers.{router_id}.rule": f"Host(`{service_domain}`)",
                f"traefik.http.routers.{router_id}.entrypoints": "websecure",
                f"traefik.http.routers.{router_id}.middlewares": "redirect-to-https",
                f"traefik.http.routers.{router_id}.tls": "true",
                f"traefik.http.routers.{router_id}.service": service_id,
                f"traefik.http.services.{service_id}.loadbalancer.server.port": str(service.port)
            })
            
            if self.config.cert_mode == "letsencrypt":
                labels[f"traefik.http.routers.{router_id}.tls.certresolver"] = "letsencrypt"
                
        return labels

    def environment(self) -> Dict[str, str]:
        """
        Generate environment variables for the container.
        """
        return {
            "USER_NAME": getpass.getuser(),
            "USER_PASS": getpass.getpass("Enter password: "),
            "USER_UID": str(os.getuid()),
            "USER_GID": str(os.getgid()),
            "LOG_DIR": "/var/log/ispawn",
            "SERVICES": ",".join(s.value for s in self.image_config.services),
            "REQUIRED_GROUP": self.group
        }

    def get_service_domain(self, service: Service) -> str:
        """
        Generate service domain name.
        
        Args:
            service: Service type
            
        Returns:
            str: Service domain name
        """
        return f"{self.config.domain_prefix}{service.value}-{self.raw_name}.{self.config.domain}"
