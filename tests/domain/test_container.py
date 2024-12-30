import pytest
from pathlib import Path
from ispawn.domain.container import ContainerConfig, Service
from ispawn.domain.exceptions import ValidationError

@pytest.fixture
def basic_config():
    """Create a basic container configuration for testing."""
    return ContainerConfig(
        name="test",
        ispawn_prefix="ispawn",
        network_name="ispawn-network",
        image="test:latest",
        services=[Service.RSTUDIO, Service.JUPYTER],
        username="testuser",
        password="testpass",
        volumes=["/test/vol1","/test/vol2"],
        uid=1000,
        gid=1000,
        domain="ispawn.localhost"
    )

def test_container_basic_properties(basic_config):
    """Test basic container properties are set correctly."""
    assert basic_config.raw_name == "test"
    assert basic_config.container_name == "ispawn-test"
    assert basic_config.image == "test:latest"
    assert len(basic_config.services) == 2
    assert Service.RSTUDIO in basic_config.services
    assert Service.JUPYTER in basic_config.services
    assert Service.VSCODE not in basic_config.services

def test_container_labels(basic_config):
    """Test container label generation."""
    labels = basic_config.get_labels()
    
    # Check base labels
    assert "traefik.enable=true" in labels
    assert "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https" in labels

    # Check service-specific labels
    assert f"traefik.http.services.rstudio-{basic_config.raw_name}.loadbalancer.server.port=8787" in labels
    assert f"traefik.http.services.jupyter-{basic_config.raw_name}.loadbalancer.server.port=8888" in labels

def test_container_environment(basic_config):
    """Test container environment variable generation."""
    env = basic_config.get_environment()
    
    assert env["USERNAME"] == "testuser"
    assert env["PASSWORD"] == "testpass"
    assert env["UID"] == "1000"
    assert env["GID"] == "1000"

def test_container_volume_mounts(basic_config):
    """Test volume mount generation."""
    mounts = basic_config.get_volume_mounts()
    assert len(mounts) == 2
    assert mounts[0] == f"/test/vol1:/mnt/host/test/vol1"

def test_container_service_urls(basic_config):
    """Test service URL generation."""
    urls = basic_config.get_service_urls()
    
    assert Service.RSTUDIO in urls
    assert Service.JUPYTER in urls
    assert Service.VSCODE not in urls
    
    assert urls[Service.RSTUDIO] == f"https://rstudio-{basic_config.raw_name}.ispawn.localhost"
    assert urls[Service.JUPYTER] == f"https://jupyter-{basic_config.raw_name}.ispawn.localhost?token=testpass"

def test_container_config_defaults():
    """Test container configuration defaults."""
    config = ContainerConfig(
        name="test",
        ispawn_prefix="ispawn",
        network_name="ispawn-network",
        image="test:latest",
        services=[Service.RSTUDIO],
        username="testuser",
        password="testpass",
        uid=1000,
        gid=1000,
        domain="ispawn.localhost"
    )
    
    assert config.dns == ["8.8.8.8", "8.8.4.4"]
    assert len(config.volumes) == 1
    assert config.volumes[0].startswith(str(Path.home()))
    assert config.host_prefix == "/mnt/host"

def test_container_config_string_services():
    """Test container configuration with string service names."""
    config = ContainerConfig(
        name="test",
        ispawn_prefix="ispawn",
        network_name="ispawn-network",
        image="test:latest",
        services=["rstudio", "jupyter"],  # String service names
        username="testuser",
        password="testpass",
        uid=1000,
        gid=1000,
        domain="ispawn.localhost"
    )
    
    assert isinstance(config.services[0], Service)
    assert config.services[0] == Service.RSTUDIO
    assert config.services[1] == Service.JUPYTER

def test_container_config_invalid_service():
    """Test that invalid service names raise an error."""
    with pytest.raises(ValueError):
        ContainerConfig(
            name="test",
            ispawn_prefix="ispawn",
            network_name="ispawn-network",
            image="test:latest",
            services=["invalid_service"],
            username="testuser",
            password="testpass",
            uid=1000,
            gid=1000,
            domain="ispawn.localhost"
        )

def test_container_config_custom_dns():
    """Test container configuration with custom DNS servers."""
    config = ContainerConfig(
        name="test",
        ispawn_prefix="ispawn",
        network_name="ispawn-network",
        image="test:latest",
        services=[Service.RSTUDIO],
        username="testuser",
        password="testpass",
        uid=1000,
        gid=1000,
        domain="ispawn.localhost",
        dns=["1.1.1.1", "1.0.0.1"]
    )
    
    assert config.dns == ["1.1.1.1", "1.0.0.1"]

def test_container_config_custom_volumes():
    """Test container configuration with custom volumes."""
    test_volumes = ["/test/path1", "/test/path2"]
    config = ContainerConfig(
        name="test",
        ispawn_prefix="ispawn",
        network_name="ispawn-network",
        image="test:latest",
        services=[Service.RSTUDIO],
        username="testuser",
        password="testpass",
        uid=1000,
        gid=1000,
        domain="ispawn.localhost",
        volumes=test_volumes
    )
    
    assert len(config.volumes) == 2
    assert config.volumes[0] == f"/test/path1:/mnt/host/test/path1"
    assert config.volumes[1] == f"/test/path2:/mnt/host/test/path2"
