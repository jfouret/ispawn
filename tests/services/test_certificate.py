import pytest
from pathlib import Path
import subprocess

from ispawn.services.certificate import CertificateService
from ispawn.domain.proxy import ProxyConfig, ProxyMode, CertMode
from ispawn.domain.exceptions import CertificateError

@pytest.fixture
def cert_service():
    """Create a CertificateService instance."""
    return CertificateService()

@pytest.fixture
def cert_dir(tmp_path):
    """Create a temporary directory for certificates."""
    cert_dir = tmp_path / "certs"
    cert_dir.mkdir()
    return cert_dir

@pytest.fixture
def local_config(cert_dir):
    """Create a local proxy configuration."""
    return ProxyConfig(
        mode=ProxyMode.LOCAL.value,
        domain="test.local",
        cert_dir=str(cert_dir)
    )

@pytest.fixture
def remote_config(cert_dir):
    """Create a remote proxy configuration."""
    return ProxyConfig(
        mode=ProxyMode.REMOTE.value,
        domain="example.com",
        cert_dir=str(cert_dir),
        cert_mode=CertMode.PROVIDED.value
    )

def test_setup_remote_certificates_directory(cert_service, remote_config):
    """Test remote certificate directory setup."""
    cert_service.setup_certificates(remote_config)
    
    # Test both existence and permissions
    cert_dir = Path(remote_config.cert_dir)
    assert cert_dir.exists(), "Certificate directory was not created"
    assert oct(cert_dir.stat().st_mode)[-3:] == '700', "Incorrect directory permissions"

def test_validate_certificates_missing_cert(cert_service, cert_dir):
    """Test certificate validation with missing certificate."""
    with pytest.raises(CertificateError, match="Certificate file.*not found"):
        cert_service.validate_certificates(cert_dir)

def test_validate_certificates_missing_key(cert_service, cert_dir):
    """Test certificate validation with missing key."""
    (cert_dir / "cert.pem").touch()
    
    with pytest.raises(CertificateError, match="Private key file.*not found"):
        cert_service.validate_certificates(cert_dir)

def test_setup_certificates_no_cert_dir(cert_service):
    """Test setup without certificate directory."""
    config = ProxyConfig(mode=ProxyMode.LOCAL.value, domain="test.local")
    with pytest.raises(CertificateError, match="Certificate directory not specified"):
        cert_service.setup_certificates(config)

def test_setup_certificates_letsencrypt_no_email(cert_service, cert_dir):
    """Test Let's Encrypt setup without email."""
    # Create config with provided certs first to avoid constructor error
    config = ProxyConfig(
        mode=ProxyMode.REMOTE.value,
        domain="example.com",
        cert_dir=str(cert_dir),
        cert_mode=CertMode.PROVIDED.value
    )
    
    # Override cert_mode to test service behavior
    config.cert_mode = CertMode.LETSENCRYPT
    
    with pytest.raises(CertificateError, match="Email required for Let's Encrypt certificates"):
        cert_service.setup_certificates(config)

@pytest.mark.skipif(
    subprocess.run(["which", "mkcert"], capture_output=True).returncode != 0,
    reason="mkcert is not installed"
)
def test_setup_local_certificates(cert_service, local_config):
    """Test local certificate setup with mkcert."""
    cert_service.setup_certificates(local_config)
    
    cert_dir = Path(local_config.cert_dir)
    cert_path = cert_dir / "cert.pem"
    key_path = cert_dir / "key.pem"
    
    # Verify files were created
    assert cert_path.exists(), "Certificate file was not created"
    assert key_path.exists(), "Key file was not created"
    
    # Verify permissions
    assert oct(cert_path.stat().st_mode)[-3:] == '600', "Incorrect certificate permissions"
    assert oct(key_path.stat().st_mode)[-3:] == '600', "Incorrect key permissions"

@pytest.mark.integration
def test_setup_remote_certificates_letsencrypt():
    """
    Test Let's Encrypt certificate setup.
    
    Requirements:
    - Public domain with DNS access
    - Port 80/443 access
    - Root access
    """
    pytest.skip("Integration test requiring public domain and Let's Encrypt access")
