import pytest
from unittest.mock import Mock, patch
import docker
from pathlib import Path
from docker.models.containers import Container as DockerContainer
from docker.models.networks import Network

from ispawn.services.docker import DockerService
from ispawn.domain.container import ContainerConfig, Service
from ispawn.domain.exceptions import ContainerError, NetworkError, ImageError

@pytest.fixture
def mock_docker_client(mocker):
    """Create a mock Docker client."""
    mock_client = mocker.patch('docker.from_env')
    mock_client.return_value.networks = mocker.MagicMock()
    mock_client.return_value.containers = mocker.MagicMock()
    mock_client.return_value.images = mocker.MagicMock()
    return mock_client.return_value

@pytest.fixture
def docker_service(mock_docker_client):
    """Create DockerService instance with mocked client."""
    return DockerService()

@pytest.fixture
def test_container():
    """Create a test container configuration."""
    return ContainerConfig(
        name="test",
        name_prefix="ispawn",
        network_name="test-network",
        image="test:latest",
        services=[Service.RSTUDIO, Service.JUPYTER],
        username="testuser",
        password="testpass",
        uid=1000,
        gid=1000,
        domain="ispawn.test"
    )

def test_create_network(docker_service, mock_docker_client):
    """Test network creation."""
    network_name = "test-network"
    subnet = "172.30.0.0/24"
    
    docker_service.create_network(network_name, subnet)
    
    mock_docker_client.networks.create.assert_called_once_with(
        network_name,
        driver="bridge",
        ipam=docker.types.IPAMConfig(
            pool_configs=[docker.types.IPAMPool(subnet=subnet)]
        ),
        labels={"created_by": "ispawn"}
    )

def test_create_network_error(docker_service, mock_docker_client):
    """Test network creation error handling."""
    mock_docker_client.networks.create.side_effect = docker.errors.APIError("network error")
    
    with pytest.raises(NetworkError, match="Failed to create network test-network"):
        docker_service.create_network("test-network", "172.30.0.0/24")

def test_get_network(docker_service, mock_docker_client, mocker):
    """Test getting an existing network."""
    mock_network = mocker.MagicMock()
    mock_docker_client.networks.list.return_value = [mock_network]
    
    network = docker_service.get_network("test-network")
    assert network == mock_network
    
    mock_docker_client.networks.list.assert_called_once_with(
        filters={"name": "test-network"}
    )

def test_get_network_not_found(docker_service, mock_docker_client):
    """Test getting a non-existent network."""
    mock_docker_client.networks.list.return_value = []
    
    network = docker_service.get_network("test-network")
    assert network is None

def test_run_container(docker_service, mock_docker_client, test_container):
    """Test running a container."""
    # Setup mock for container check
    mock_docker_client.containers.list.return_value = []
    
    docker_service.run_container(test_container)
    
    # Verify container run was called with correct parameters
    mock_docker_client.containers.run.assert_called_once()
    call_args = mock_docker_client.containers.run.call_args[1]
    
    assert call_args["name"] == test_container.container_name
    assert call_args["image"] == test_container.image
    assert call_args["detach"] is True
    assert call_args["network"] == test_container.network_name
    assert all(label in call_args["labels"] for label in test_container.get_labels())

def test_run_container_already_exists(docker_service, mock_docker_client, test_container, mocker):
    """Test running a container that already exists."""
    # Setup mock for existing container
    mock_existing = mocker.MagicMock()
    mock_docker_client.containers.list.return_value = [mock_existing]
    
    with pytest.raises(ContainerError, match="Container ispawn-test already exists"):
        docker_service.run_container(test_container, force=False)

def test_run_container_force_replace(docker_service, mock_docker_client, test_container, mocker):
    """Test force replacing an existing container."""
    # Setup mock for existing container
    mock_existing = mocker.MagicMock()
    mock_docker_client.containers.list.return_value = [mock_existing]
    
    docker_service.run_container(test_container, force=True)
    
    # Verify container was removed and new one created
    mock_existing.remove.assert_called_once_with(force=True)
    mock_docker_client.containers.run.assert_called_once()

def test_list_containers(docker_service, mock_docker_client, mocker):
    """Test listing containers."""
    # Setup mock containers
    mock_container = mocker.MagicMock()
    mock_container.name = "ispawn-test"
    mock_container.image.tags = ["test:latest"]
    mock_container.status = "running"
    mock_container.short_id = "abc123"
    
    mock_docker_client.containers.list.return_value = [mock_container]
    
    containers = docker_service.list_containers()
    
    assert len(containers) == 1
    assert containers[0]["name"] == "ispawn-test"
    assert containers[0]["image"] == "test:latest"
    assert containers[0]["status"] == "running"
    assert containers[0]["id"] == "abc123"

def test_get_image(docker_service, mock_docker_client, mocker):
    """Test checking if an image exists."""
    mock_docker_client.images.get.return_value = mocker.MagicMock()
    
    assert docker_service.get_image("test:latest") is True
    mock_docker_client.images.get.assert_called_once_with("test:latest")

def test_get_image_not_found(docker_service, mock_docker_client):
    """Test checking for a non-existent image."""
    mock_docker_client.images.get.side_effect = docker.errors.ImageNotFound("not found")
    
    assert docker_service.get_image("test:latest") is False

@pytest.mark.integration
class TestDockerIntegration:
    """Integration tests that require a running Docker daemon."""
    
    @pytest.fixture
    def docker_service_real(self):
        """Create a real DockerService instance."""
        return DockerService()
    
    def _find_available_subnet(self, docker_service_real, base_name: str) -> tuple[str, str]:
        """Try to find an available subnet in the range 172.16-31.0.0/24."""
        for i in range(16, 32):
            network_name = f"{base_name}-{i}"
            subnet = f"172.{i}.0.0/24"
            try:
                network = docker_service_real.create_network(network_name, subnet)
                return network_name, subnet
            except NetworkError as e:
                if "Pool overlaps" not in str(e):
                    raise
                continue
        raise NetworkError("No available subnets found in range 172.16-31.0.0/24")

    def test_network_lifecycle(self, docker_service_real):
        """Test creating and removing a network."""
        network_name, subnet = self._find_available_subnet(docker_service_real, "ispawn-test-network")
        try:
            # Verify network exists
            found_network = docker_service_real.get_network(network_name)
            assert found_network is not None
            assert found_network.name == network_name
            
        finally:
            # Cleanup
            network = docker_service_real.get_network(network_name)
            if network:
                network.remove()
    
    def test_container_lifecycle(self, docker_service_real):
        """Test running and managing a container."""
        # Find available subnet and create network
        network_name, subnet = self._find_available_subnet(docker_service_real, "ispawn-integration-test")
        
        # Use Ubuntu image with a command that keeps container running
        config = ContainerConfig(
            name="integration-test",
            name_prefix="ispawn",
            network_name=network_name,
            image="ubuntu:20.04",
            services=[Service.RSTUDIO],
            username="test",
            password="test",
            uid=1000,
            gid=1000,
            domain="ispawn.test"
        )
        
        try:
            # Ensure network exists
            docker_service_real.ensure_network(network_name, subnet)
            
            # Run container with a command that keeps it running
            docker_container = docker_service_real.run_container(
                config=config,
                command="tail -f /dev/null",  # Keep container running
            )
            assert docker_container is not None
            
            # Give container time to start
            import time
            time.sleep(2)
            
            # Verify container is running
            found_container = docker_service_real.get_container(config.container_name)
            assert found_container is not None
            assert found_container.status == "running"
            
            # List containers
            containers = docker_service_real.list_containers()
            assert any(c["name"] == config.container_name for c in containers)
            
        finally:
            # Cleanup
            docker_service_real.remove_container(config.container_name)
            network = docker_service_real.get_network(network_name)
            if network:
                network.remove()
