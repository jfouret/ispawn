import os
from pathlib import Path
from typing import Optional
from ispawn.config import Config
from ispawn.services.docker import DockerService

def logs_command(config: Config, container_name: str, follow: bool = False) -> None:
    """Display logs for a container.
    
    Args:
        config: Configuration instance
        container_name: Name of the container
        follow: Whether to follow the logs (like tail -f)
    """
    try:
        # Get container info
        docker_service = DockerService()
        container = docker_service.get_container(f"ispawn-{container_name}")
        if not container:
            raise RuntimeError(f"Container {container_name} not found")

        # Find latest log directory for this container
        log_dirs = sorted(config.log_dir.glob(f"{container_name}.*"))
        if not log_dirs:
            raise RuntimeError(f"No logs found for container {container_name}")
        
        latest_log_dir = log_dirs[-1]
        
        # Print Docker container logs
        print("=== Docker Container Logs ===")
        print(container.logs().decode('utf-8'))
        
        # Print service logs
        print("\n=== Service Logs ===")
        
        # Read entrypoint log
        entrypoint_log = latest_log_dir / "entrypoint.log"
        if entrypoint_log.exists():
            print("\n--- Entrypoint Log ---")
            if follow:
                os.system(f"tail -f {entrypoint_log}")
            else:
                print(entrypoint_log.read_text())
        
        # Read service-specific logs
        for service_dir in ["jupyter", "rstudio", "vscode"]:
            service_log = latest_log_dir / service_dir / f"{service_dir}.log"
            if service_log.exists():
                print(f"\n--- {service_dir.title()} Log ---")
                if follow:
                    os.system(f"tail -f {service_log}")
                else:
                    print(service_log.read_text())
                    
    except Exception as e:
        raise RuntimeError(f"Failed to get logs: {str(e)}")
