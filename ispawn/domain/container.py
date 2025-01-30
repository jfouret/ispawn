from typing import List, Dict, Union, Optional, Tuple
from pathlib import Path
import os
import getpass
import pwd
import grp

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
        group: Optional[str] = None,
        user: Optional[str] = None,
        sudo: bool = True
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
        self.sudo = sudo
        
        # Handle user for container execution
        self.user = user or getpass.getuser()
        try:
            pwd_entry = pwd.getpwnam(self.user)
            self.user_uid = pwd_entry.pw_uid
            self.user_gid = pwd_entry.pw_gid
        except KeyError as e:
            raise ValueError(f"User {self.user} not found in the system")
            
        # Keep service group separate from user's system group
        self.group = group or self.user
        
        # Create log and volume directories
        log_dir = Path(config.user_root_dir) / self.container_name / "logs"
        vol_dir = Path(config.user_root_dir) / self.container_name / "volumes"
        log_dir.mkdir(parents=True, exist_ok=True)
        vol_dir.mkdir(parents=True, exist_ok=True)
        self.vol_dir = str(vol_dir)
        self.log_dir = str(log_dir)
        
        def _has_rwx_permissions(path: Path) -> bool:
            """
            Check if current user has rwx permissions on a directory.
            
            Args:
                path: Path to check permissions for
                
            Returns:
                bool: True if user has rwx access, False otherwise
            """
            try:
                stat = path.stat()
                mode = stat.st_mode
                uid = stat.st_uid
                gid = stat.st_gid
                
                # Check user permissions
                if uid == self.user_uid:
                    if mode & 0o700 == 0o700:  # User has rwx
                        return True
                    
                # Check group permissions
                user_groups = [g.gr_gid for g in grp.getgrall() if self.user in g.gr_mem]
                if gid in user_groups:
                    if mode & 0o070 == 0o070:  # Group has rwx
                        return True
                
                return False
                
            except (PermissionError, FileNotFoundError):
                return False

        def _ensure_source_directory(src_path: str) -> Tuple[bool, str]:
            """
            Ensure a source directory exists, creating it if possible.
            
            Args:
                src_path: Path to check/create
                
            Returns:
                Tuple of (success, message)
            """
            path = Path(src_path)
            if path.exists():
                if not path.is_dir():
                    return False, f"Source path {src_path} exists but is not a directory"
                if not self._has_rwx_permissions(path):
                    return False, f"User {self.user} does not have rwx permissions on directory {src_path}"
                return True, ""
                
            try:
                path.mkdir(parents=True, exist_ok=True)
                if not self._has_rwx_permissions(path):
                    return False, f"Created directory {src_path} but user {self.user} does not have rwx permissions"
                return True, ""
            except PermissionError:
                return False, f"Permission denied creating directory {src_path}"
            except Exception as e:
                return False, f"Failed to create directory {src_path}: {str(e)}"

        # Process volumes
        self.volumes = config.volumes.copy()
        self.volumes.extend(volumes)
        self.volumes.append([f"{self.log_dir}", "/var/log/ispawn"])
        
        # Check and create source directories for user volumes
        for volume in self.volumes:
            src = volume[0]
            success, message = _ensure_source_directory(src)
            if not success:
                print(f"INFO: {message}")
        
        # Add service-specific volumes last
        for service in self.image_config.services:
            service_volumes = service.volumes
            for host_dir, container_path in service_volumes.items():
                # Create and check service-specific directory
                service_vol_dir = Path(self.vol_dir) / service.value / host_dir
                success, message = _ensure_source_directory(service_vol_dir)
                if not success:
                    print(f"INFO: {message}")
                # Add volume mapping
                self.volumes.append([str(service_vol_dir), container_path.replace("~", f"{self.config.home_prefix}/{self.user}")])

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
            "USER_NAME": self.user,
            "USER_PASS": getpass.getpass("Enter password: "),
            "USER_UID": str(self.user_uid),
            "USER_GID": str(self.user_gid),
            "LOG_DIR": "/var/log/ispawn",
            "SERVICES": ",".join(s.value for s in self.image_config.services),
            "REQUIRED_GROUP": self.group,
            "USER_AS_SUDO": "1" if self.sudo else "0"
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
