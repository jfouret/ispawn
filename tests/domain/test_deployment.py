import pytest
from ispawn.domain.deployment import Mode, CertMode, DeploymentConfig

@pytest.fixture(params=[
    # Basic local configuration
    {
        "mode": "local",
        "domain": "ispawn.localhost",
        "subnet": "172.30.0.0/24"
    },
    # Remote configuration with Let's Encrypt
    {
        "mode": "remote",
        "domain": "example.com",
        "subnet": "172.30.0.0/24",
        "cert_mode": "letsencrypt",
        "cert_dir": "/path/to/certs",
        "email": "admin@example.com"
    },
    # Remote configuration with provided certificates
    {
        "mode": "remote",
        "domain": "example.org",
        "subnet": "172.31.0.0/24",
        "cert_mode": "provided",
        "cert_dir": "/path/to/certs"
    }
])
def valid_args(request):
    """Provide different valid argument configurations."""
    return request.param

@pytest.fixture
def deployment_config(valid_args):
    """Create a deployment configuration from valid arguments."""
    return DeploymentConfig(**valid_args)

def test_mode_from_str():
    """Test Mode enum creation from string."""
    assert Mode.from_str("local") == Mode.LOCAL
    assert Mode.from_str("remote") == Mode.REMOTE
    assert Mode.from_str("LOCAL") == Mode.LOCAL
    assert Mode.from_str("REMOTE") == Mode.REMOTE

def test_invalid_mode():
    """Test invalid mode handling."""
    with pytest.raises(ValueError, match="Invalid mode"):
        Mode.from_str("invalid")

def test_cert_mode_from_str():
    """Test CertMode enum creation from string."""
    assert CertMode.from_str("letsencrypt") == CertMode.LETSENCRYPT
    assert CertMode.from_str("provided") == CertMode.PROVIDED
    assert CertMode.from_str("LETSENCRYPT") == CertMode.LETSENCRYPT
    assert CertMode.from_str("PROVIDED") == CertMode.PROVIDED

def test_invalid_cert_mode():
    """Test invalid certificate mode handling."""
    with pytest.raises(ValueError, match="Invalid certificate mode"):
        CertMode.from_str("invalid")

def test_deployment_basic_properties(deployment_config, valid_args):
    """Test basic deployment properties are set correctly."""
    assert deployment_config.domain == valid_args["domain"]
    assert deployment_config.subnet == valid_args["subnet"]
    assert deployment_config.mode == Mode.from_str(valid_args["mode"])

def test_deployment_cert_properties(deployment_config, valid_args):
    """Test certificate-related properties."""
    if "cert_mode" in valid_args:
        assert deployment_config.cert_mode == CertMode.from_str(valid_args["cert_mode"])
    if "cert_dir" in valid_args:
        assert deployment_config.cert_dir == valid_args["cert_dir"]
    if "email" in valid_args:
        assert deployment_config.email == valid_args["email"]

def test_is_local(deployment_config, valid_args):
    """Test is_local property."""
    assert deployment_config.is_local == (valid_args["mode"] == "local")

def test_requires_email(deployment_config, valid_args):
    """Test requires_email property."""
    expected = (
        valid_args["mode"] == "remote" and 
        valid_args.get("cert_mode", "letsencrypt") == "letsencrypt"
    )
    assert deployment_config.requires_email == expected

def test_default_cert_mode():
    """Test default certificate mode based on deployment mode."""
    local_config = DeploymentConfig(mode="local")
    assert local_config.cert_mode is None

    remote_config = DeploymentConfig(mode="remote")
    assert remote_config.cert_mode == CertMode.LETSENCRYPT

def test_email_handling():
    """Test email handling based on deployment mode."""
    local_config = DeploymentConfig(mode="local", email="test@example.com")
    assert local_config.email is None  # Email ignored in local mode

    remote_config = DeploymentConfig(
        mode="remote",
        cert_mode="letsencrypt",
        email="test@example.com"
    )
    assert remote_config.email == "test@example.com"
