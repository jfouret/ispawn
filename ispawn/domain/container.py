from typing import List, Dict, Union
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
    """

    def __init__(
        self,
        name: str,
        config: Config,
        image_config: ImageConfig,
        volumes: List[List[str]]
    ):
        """
        Initialize container configuration.
        
        Args:
        
        Raises:
            ValueError: If cert_mode is invalid
        """

        self.config = config
        self.raw_name = name
        self.container_name = f"{config.container_name_prefix}{name}"
        self.image_config = image_config
        log_dir = Path(config.base_log_dir) / self.container_name
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = str(log_dir)
        
        # Process volumes
        self.volumes = config.volumes
        self.volumes.extend(volumes)
        self.volumes.append([f"{self.log_dir}", "/var/log/ispawn"])

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
            "SERVICES": ",".join(s.value for s in self.image_config.services)
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
