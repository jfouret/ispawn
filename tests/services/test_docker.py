import pytest
import time

from ispawn.services.container import DockerService
from ispawn.domain.container import ContainerConfig, Service
from ispawn.domain.proxy import ProxyConfig, ProxyMode, CertMode
from ispawn.domain.exceptions import ContainerError, NetworkError

@pytest.fixture
def docker_service():
    """Create DockerService instance."""
    return DockerService()

@pytest.fixture
def proxy_config():
    """Create a test proxy configuration."""
    return ProxyConfig(
        mode=ProxyMode.LOCAL.value,
        domain="ispawn.test",
        subnet="172.30.0.0/24",
        name="ispawn-test"
    )

@pytest.fixture
def test_container(proxy_config):
    """Create a test container configuration."""
    return ContainerConfig(
        name="test-container",
        name_prefix="ispawn",
        network_name=proxy_config.network_name,
        image="ubuntu:20.04",  # Use Ubuntu as it's likely to be available
        services=[Service.RSTUDIO],
        username="test",
        password="test",
        uid=1000,
        gid=1000,
        domain=proxy_config.domain,
        dns=["8.8.8.8"],
        volumes=[],
        host_prefix="/tmp/ispawn",
        log_base_dir="/tmp/ispawn/logs",
        cert_mode=CertMode.PROVIDED.value
    )

def _cleanup_network(docker_service, name: str):
    """Clean up a network if it exists."""
    network = docker_service.get_network(name)
    if network:
        try:
            network.remove()
        except:
            pass  # Ignore cleanup errors

def _create_proxy_config(base_name: str, subnet: str) -> ProxyConfig:
    """Create a proxy config with specific network settings."""
    return ProxyConfig(
        mode=ProxyMode.LOCAL.value,
        domain="ispawn.test",
        subnet=subnet,
        name=base_name
    )

def _find_available_subnet(docker_service) -> tuple[ProxyConfig, str]:
    """Try to find an available subnet in the range 172.16-31.0.0/24."""
    for i in range(16, 32):
        network_name = f"ispawn-test-{i}"
        subnet = f"172.{i}.0.0/24"
        
        # Clean up any existing network with this name
        _cleanup_network(docker_service, network_name)
        
        # Create proxy config for this subnet
        config = _create_proxy_config(network_name, subnet)
        
        try:
            docker_service.create_network(config)
            return config, subnet
        except NetworkError as e:
            if "Pool overlaps" not in str(e):
                raise
            continue
    raise NetworkError("No available subnets found in range 172.16-31.0.0/24")

def test_network_lifecycle(docker_service):
    """Test creating and removing a network."""
    config, _ = _find_available_subnet(docker_service)
    try:
        # Verify network exists
        found_network = docker_service.get_network(config.network_name)
        assert found_network is not None
        assert found_network.name == config.network_name
        
        # Test network not found
        assert docker_service.get_network("nonexistent-network") is None
        
    finally:
        # Cleanup
        _cleanup_network(docker_service, config.network_name)

def test_container_lifecycle(docker_service):
    """Test running and managing a container."""
    # Find available subnet and create network
    config, _ = _find_available_subnet(docker_service)
    
    # Create container config using proxy network
    container_config = ContainerConfig(
        name="test-container",
        name_prefix="ispawn",
        network_name=config.network_name,
        image="ubuntu:20.04",  # Use Ubuntu as it's likely to be available
        services=[Service.RSTUDIO],
        username="test",
        password="test",
        uid=1000,
        gid=1000,
        domain=config.domain,
        dns=["8.8.8.8"],
        volumes=[],
        host_prefix="/tmp/ispawn",
        log_base_dir="/tmp/ispawn/logs",
        cert_mode=CertMode.PROVIDED.value
    )
    
    try:
        # Ensure network exists
        docker_service.ensure_network(config)
        
        # Run container with a command that keeps it running
        docker_container = docker_service.run_container(
            config=container_config,
            command="tail -f /dev/null",  # Keep container running
        )
        assert docker_container is not None
        
        # Give container time to start
        time.sleep(2)
        
        # Verify container is running
        found_container = docker_service.get_container(container_config.container_name)
        assert found_container is not None
        assert found_container.status == "running"
        
        # Test container already exists
        with pytest.raises(ContainerError, match="Container.*already exists"):
            docker_service.run_container(container_config)
        
        # Test force replace
        new_container = docker_service.run_container(container_config, force=True)
        assert new_container is not None
        
        # List containers
        containers = docker_service.list_containers()
        assert any(c["name"] == container_config.container_name for c in containers)
        
        # Test container not found
        assert docker_service.get_container("nonexistent-container") is None
        
    finally:
        # Cleanup
        docker_service.remove_container(container_config.container_name)
        _cleanup_network(docker_service, config.network_name)

def test_image_checks(docker_service):
    """Test image existence checks."""
    # Test existing image (use Ubuntu as it's likely to be available)
    assert docker_service.get_image("ubuntu:20.04") is True
    
    # Test non-existent image
    assert docker_service.get_image("nonexistent:latest") is False
