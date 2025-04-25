import pytest
from pathlib import Path
from ispawn.domain.container import ContainerConfig, Service

@pytest.fixture(params=[
    # Basic configuration with minimal services
    {
        "name": "test",
        "name_prefix": "ispawn",
        "network_name": "ispawn-network",
        "image": "test:latest",
        "services": [Service.RSTUDIO],
        "username": "testuser",
        "password": "testpass",
        "volumes": ["/test/vol1", "/test/vol2"],
        "uid": 1000,
        "gid": 1000,
        "domain": "ispawn.localhost",
        "dns": ["8.8.8.8", "8.8.4.4"],
        "host_prefix": "/mnt/host",
        "log_base_dir": "/home/user/ispawn/logs",
        "cert_mode": "provided"
    },
    # Configuration with all services
    {
        "name": "full",
        "name_prefix": "ispawn",
        "network_name": "ispawn-network",
        "image": "full:latest",
        "services": [Service.RSTUDIO, Service.JUPYTER, Service.VSCODE],
        "username": "fulluser",
        "password": "fullpass",
        "volumes": ["/data/vol1", "/data/vol2"],
        "uid": 1001,
        "gid": 1001,
        "domain": "full.localhost",
        "dns": ["1.1.1.1", "1.0.0.1"],
        "host_prefix": "/mnt/data",
        "log_base_dir": "/var/log/ispawn",
        "cert_mode": "letsencrypt"
    },
    # Configuration with minimal volumes
    {
        "name": "minimal",
        "name_prefix": "ispawn",
        "network_name": "ispawn-network",
        "image": "minimal:latest",
        "services": [Service.JUPYTER, Service.VSCODE],
        "username": "minuser",
        "password": "minpass",
        "volumes": [],
        "uid": 1002,
        "gid": 1002,
        "domain": "min.localhost",
        "dns": ["8.8.8.8", "8.8.4.4"],
        "host_prefix": "/mnt/min",
        "log_base_dir": "/var/log/min",
        "cert_mode": "provided"
    }
])
def valid_args(request):
    """Provide different valid argument configurations."""
    return request.param

@pytest.fixture
def container_config(valid_args):
    """Create a container configuration from valid arguments."""
    return ContainerConfig(**valid_args)

def test_container_basic_properties(container_config, valid_args):
    """Test basic container properties are set correctly."""
    assert container_config.raw_name == valid_args["name"]
    assert container_config.container_name == f"{valid_args['name_prefix']}-{valid_args['name']}"
    assert container_config.image == valid_args["image"]
    assert len(container_config.services) == len(valid_args["services"])
    for service in valid_args["services"]:
        assert service in container_config.services

def test_container_labels(container_config, valid_args):
    """Test container label generation."""
    labels = container_config.get_labels()
    # Check base labels
    assert "traefik.enable=true" in labels
    assert "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https" in labels
    
    # Check service-specific labels
    for service in valid_args["services"]:
        if service == Service.RSTUDIO:
            assert f"traefik.http.services.rstudio-{valid_args['name']}.loadbalancer.server.port=8787" in labels
        elif service == Service.JUPYTER:
            assert f"traefik.http.services.jupyter-{valid_args['name']}.loadbalancer.server.port=8888" in labels
        elif service == Service.VSCODE:
            assert f"traefik.http.services.vscode-{valid_args['name']}.loadbalancer.server.port=8842" in labels

    # Check cert mode specific labels
    cert_label = "certresolver=letsencrypt" if valid_args["cert_mode"] == "letsencrypt" else ".tls=true"
    assert any(cert_label in label for label in labels)

def test_container_environment(container_config, valid_args):
    """Test container environment variable generation."""
    env = container_config.get_environment()
    assert env["USERNAME"] == valid_args["username"]
    assert env["PASSWORD"] == valid_args["password"]
    assert env["UID"] == str(valid_args["uid"])
    assert env["GID"] == str(valid_args["gid"])
    assert env["SERVICES"] == ",".join(s.value for s in valid_args["services"])

def test_container_volume_mounts(container_config, valid_args):
    """Test volume mount generation."""
    mounts = container_config.get_volume_mounts()
    # Always has at least the log volume
    assert len(mounts) == max(1,len(valid_args["volumes"])) + 1

    if valid_args["volumes"] == 0:
        volume = str(Path.home())
        expected_mount = f"{volume}:{valid_args['host_prefix']}/{volume.lstrip('/')}"
    
    for i, volume in enumerate(valid_args["volumes"]):
        expected_mount = f"{volume}:{valid_args['host_prefix']}/{volume.lstrip('/')}"
        assert mounts[i] == expected_mount

def test_container_service_urls(container_config, valid_args):
    """Test service URL generation."""
    urls = container_config.get_service_urls()
    
    for service in valid_args["services"]:
        assert service in urls
        if service == Service.JUPYTER:
            assert urls[service] == f"https://jupyter-{valid_args['name']}.{valid_args['domain']}?token={valid_args['password']}"
        elif service == Service.RSTUDIO:
            assert urls[service] == f"https://rstudio-{valid_args['name']}.{valid_args['domain']}"
        elif service == Service.VSCODE:
            assert urls[service] == f"https://vscode-{valid_args['name']}.{valid_args['domain']}"

@pytest.mark.parametrize("invalid_field,invalid_value,expected_error", [
    ("services", ["invalid_name", "rstudio"], ValueError),
    ("services", ["not_a_service"], ValueError),
    ("cert_mode", "invalid", ValueError),
    ("cert_mode", "self_signed", ValueError),
])
def test_container_config_invalid_fields(valid_args, invalid_field, invalid_value, expected_error):
    """Test that invalid field values raise appropriate errors."""
    invalid_args = valid_args.copy()
    invalid_args[invalid_field] = invalid_value
    
    with pytest.raises(expected_error):
        ContainerConfig(**invalid_args)
