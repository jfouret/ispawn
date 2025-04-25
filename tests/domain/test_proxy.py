import pytest
from ispawn.domain.proxy import ProxyMode, CertMode, ProxyConfig
from ispawn.domain.exceptions import ConfigurationError
from io import StringIO
from pathlib import Path

VALID_CONFIGS = [
    {
        "id": "local_basic",
        "params": {
            "install_mode": "user",
            "mode": "local",
            "domain": "ispawn.localhost",
            "cert_dir": "/path/to/certs",
            "subnet": "172.16.0.0/24",
            "name": "ispawn"
        }
    },
    {
        "id": "remote_letsencrypt",
        "params": {
            "install_mode": "system",
            "mode": "remote",
            "domain": "example.com",
            "cert_mode": "letsencrypt",
            "cert_dir": "/path/to/certs",
            "email": "admin@example.com",
            "subnet": "172.16.0.0/24",
            "name": "ispawn"
        }
    },
    {
        "id": "remote_provided",
        "params": {
            "install_mode": "user",
            "mode": "remote",
            "domain": "example.com",
            "cert_mode": "provided",
            "cert_dir": "/path/to/certs",
            "subnet": "172.16.0.0/24",
            "name": "ispawn"
        }
    }
]

@pytest.fixture(params=VALID_CONFIGS)
def valid_config_params(request):
    return request.param

@pytest.fixture
def valid_proxy_config(valid_config_params):
    return ProxyConfig(**valid_config_params["params"])

@pytest.fixture(params=[
    {
        "id": "remote_missing_cert_mode",
        "params": {
            "install_mode": "user",
            "mode": "remote",
            "domain": "example.com",
            "subnet": "172.16.0.0/24",
            "name": "ispawn"
        },
        "error_type": ConfigurationError,
        "error_msg": "Certificate mode is required for remote proxy"
    },
    {
        "id": "remote_letsencrypt_missing_email",
        "params": {
            "install_mode": "user",
            "mode": "remote",
            "domain": "example.com",
            "cert_mode": "letsencrypt",
            "subnet": "172.16.0.0/24",
            "name": "ispawn"
        },
        "error_type": ConfigurationError,
        "error_msg": "Email is required for Let's Encrypt certificates"
    },
    {
        "id": "local_with_email",
        "params": {
            "install_mode": "user",
            "mode": "local",
            "domain": "ispawn.localhost",
            "email": "not@needed.com",
            "subnet": "172.16.0.0/24",
            "name": "ispawn"
        },
        "error_type": ConfigurationError,
        "error_msg": "Email is not used in local proxy mode"
    },
    {
        "id": "local_without_localhost",
        "params": {
            "install_mode": "user",
            "mode": "local",
            "domain": "ispawn.test",
            "subnet": "172.16.0.0/24",
            "name": "ispawn"
        },
        "error_type": ConfigurationError,
        "error_msg": "Domain must end with '.localhost' in local proxy mode"
    },
    {
        "id": "invalid_proxy_mode",
        "params": {
            "install_mode": "user",
            "mode": "invalid",
            "domain": "example.com",
            "subnet": "172.16.0.0/24",
            "name": "ispawn"
        },
        "error_type": ValueError,
        "error_msg": "Invalid proxymode: invalid. Must be one of: local remote"
    },
    {
        "id": "invalid_cert_mode",
        "params": {
            "install_mode": "user",
            "mode": "remote",
            "domain": "example.com",
            "cert_mode": "invalid",
            "subnet": "172.16.0.0/24",
            "name": "ispawn"
        },
        "error_type": ValueError,
        "error_msg": "Invalid certmode: invalid. Must be one of: letsencrypt provided"
    }
])
def invalid_config_params(request):
    return request.param

@pytest.mark.parametrize("mode_str,expected", [
    ("local", ProxyMode.LOCAL),
    ("remote", ProxyMode.REMOTE),
    ("LOCAL", ProxyMode.LOCAL),
    ("REMOTE", ProxyMode.REMOTE)
])
def test_proxy_mode_from_str(mode_str, expected):
    """Test ProxyMode enum creation from string."""
    assert ProxyMode.from_str(mode_str) == expected

@pytest.mark.parametrize("mode_str,expected", [
    ("letsencrypt", CertMode.LETSENCRYPT),
    ("provided", CertMode.PROVIDED),
    ("LETSENCRYPT", CertMode.LETSENCRYPT),
    ("PROVIDED", CertMode.PROVIDED)
])

def test_cert_mode_from_str(mode_str, expected):
    """Test CertMode enum creation from string."""
    assert CertMode.from_str(mode_str) == expected

def test_valid_proxy_config_creation(valid_config_params):
    """Test valid proxy configurations."""
    config = ProxyConfig(**valid_config_params["params"])
    params = valid_config_params["params"]
    
    assert config.mode == ProxyMode.from_str(params["mode"])
    assert config.domain == params["domain"]
    assert config.subnet == params["subnet"]
    assert config.name == params["name"]
    assert config.network_name == f"{config.name}_internal"
    
    if params["mode"] == "remote":
        assert config.cert_mode == CertMode.from_str(params["cert_mode"])
        assert config.email == params.get("email")
        assert config.is_local is False
        assert config.requires_email == (params.get("cert_mode") == "letsencrypt")
    else:
        assert config.cert_mode is None
        assert config.email is None
        assert config.is_local is True
        assert config.requires_email is False

    if params["install_mode"] == "system":
        assert config.is_system_install is True
        assert config.config_dir == "/etc/ispawn"
        assert config.config_path == "/etc/ispawn/config.yaml"
    else:
        assert config.is_system_install is False
        assert config.config_dir == str(Path.home() / ".ispawn")
        assert config.config_path == str(Path.home() / ".ispawn/config.yaml")

def test_invalid_proxy_config_creation(invalid_config_params):
    """Test invalid proxy configurations."""
    with pytest.raises(invalid_config_params["error_type"], match=invalid_config_params["error_msg"]):
        ProxyConfig(**invalid_config_params["params"])

def test_proxy_config_yaml_serialization(valid_proxy_config):
    """Test ProxyConfig serialization to and from YAML."""
    # Test serialization
    yaml_io = StringIO()
    valid_proxy_config.to_yaml(yaml_io)
    yaml_content = yaml_io.getvalue()
    
    # Test deserialization
    yaml_io = StringIO(yaml_content)
    loaded_config = ProxyConfig.from_yaml(yaml_io)
    
    # Verify the loaded config matches the original
    assert loaded_config == valid_proxy_config

@pytest.fixture
def config_map():
    """Create a map of config IDs to ProxyConfig instances."""
    return {cfg["id"]: ProxyConfig(**cfg["params"]) for cfg in VALID_CONFIGS}

@pytest.mark.parametrize("config1_id,config2_id,should_be_equal", [
    ("local_basic", "local_basic", True),
    ("remote_letsencrypt", "remote_letsencrypt", True),
    ("local_basic", "remote_letsencrypt", False),
    ("remote_letsencrypt", "remote_provided", False)
])
def test_proxy_config_equality(config_map, config1_id, config2_id, should_be_equal):
    """Test ProxyConfig equality comparison."""
    config1 = config_map[config1_id]
    config2 = config_map[config2_id]
    
    assert (config1 == config2) == should_be_equal
    assert (config1 != "not a config") is True
