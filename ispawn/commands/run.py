import os
import sys
import getpass
from pathlib import Path
from typing import List, Optional

from ispawn.config import Config
from ispawn.domain.container import Service, ContainerConfig
from ispawn.services.docker import DockerService
from ispawn.domain.exceptions import ContainerError, ConfigurationError, ImageError
from ispawn.domain.security import generate_password

def parse_services(services: str) -> List[Service]:
    """Parse and validate service names.
    
    Args:
        services: List of service names (comma or space separated)
        
    Returns:
        List of Service enums
        
    Raises:
        ValueError: If any service name is invalid
    """
    if isinstance(services, str):
        # Split by comma and/or space, filter empty strings
        services = [s.strip() for s in services.replace(',', ' ').split() if s.strip()]
    return [Service.from_str(s) for s in services]

def run_container(args) -> None:
    """Run a container with the specified services."""
    try:
        # Initialize services
        config = Config()
        docker = DockerService()
        
        # Parse and validate services
        services = parse_services(args.services)
        
        # Setup container configuration
        container_config = ContainerConfig(
            name=args.name,
            name_prefix=config.container_prefix,
            network_name=config.network_name,
            image=args.image,
            services=services,
            username=args.username or getpass.getuser(),
            password=args.password or generate_password(8),  # Use 8 chars for backward compatibility
            uid=args.uid or os.getuid(),
            gid=args.gid or os.getgid(),
            domain=config.domain,
            dns=args.dns.split(',') if args.dns else None,
            volumes=args.volumes.split(',') if args.volumes else None,
            log_base_dir=config.log_dir,
            cert_mode=config.cert_mode.value
        )
                
        # Verify image exists
        if not docker.get_image(container_config.image):
            print(f"Image '{container_config.image}' not found. Please build the image first using 'ispawn image build'.")
            sys.exit(1)
        
        # Ensure network exists
        docker.ensure_network(config.network_name, config.subnet)
        
        # Run container
        docker_container = docker.run_container(
            config=container_config,
            force=args.force
        )
        
        # Print access information
        print(f"Docker container '{container_config.container_name}' is running.")
        print("Access services at:")
        print("---")
        
        urls = container_config.get_service_urls()
        for service, url in urls.items():
            if service == Service.RSTUDIO:
                print(f" - {service.value}: {url}")
                print(f"   - Username: {container_config.username}")
                print(f"   - Password: {container_config.password}")
            else:
                print(f" - {service.value}: {url}")
            print("---")
            
    except (ContainerError, ConfigurationError, ImageError) as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)
