"""
Service Layer Test Example

This test module demonstrates testing a service that:
1. Interacts with external systems (filesystem, system commands)
2. Has side effects (creates files, modifies permissions)
3. Requires different testing approaches based on environment

Key testing concepts demonstrated:
- Combining unit tests and integration tests
- Using pytest fixtures for setup/teardown
- Mocking external dependencies
- Handling environment-dependent tests
- Testing error conditions
"""

import pytest
from pathlib import Path
import subprocess
import os
from unittest.mock import patch

from ispawn.services.certificate import CertificateService
from ispawn.domain.exceptions import CertificateError

# Fixtures provide reusable test setup and teardown

@pytest.fixture
def cert_service():
    """
    Create a CertificateService instance.
    
    This is a simple fixture that just instantiates the service.
    More complex fixtures might:
    - Set up mock dependencies
    - Configure the service
    - Provide cleanup
    """
    return CertificateService()

@pytest.fixture
def cert_dir(tmp_path):
    """
    Create a temporary directory for certificates.
    
    This fixture demonstrates:
    1. Using pytest's tmp_path fixture
    2. Creating test-specific directories
    3. Automatic cleanup (tmp_path is cleaned up by pytest)
    """
    cert_dir = tmp_path / "certs"
    cert_dir.mkdir()
    return cert_dir

def test_setup_remote_certificates_directory(cert_service, cert_dir):
    """
    Test remote certificate directory setup.
    
    This is a basic unit test that verifies:
    1. Directory creation
    2. Permission setting
    3. No external system requirements
    """
    cert_service.setup_remote_certificates(cert_dir)
    
    # Test both existence and permissions
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

def test_setup_local_certificates_mkcert_not_installed(cert_service, cert_dir):
    """
    Test local certificate setup when mkcert is not installed.
    
    This test demonstrates:
    1. Mocking external commands (subprocess.run)
    2. Testing error conditions
    3. Verifying error messages
    4. Using context managers for mocking
    """
    # Mock the subprocess.run command that checks for mkcert
    with patch('subprocess.run') as mock_run:
        # Configure mock to simulate mkcert not being installed
        mock_run.side_effect = subprocess.CalledProcessError(1, ["which", "mkcert"])
        
        # Verify the correct error is raised with the expected message
        with pytest.raises(CertificateError, match="mkcert is not installed"):
            cert_service.setup_local_certificates("test.local", cert_dir)

@pytest.mark.skipif(  # Only run this test if mkcert is installed
    subprocess.run(["which", "mkcert"], capture_output=True).returncode != 0,
    reason="mkcert is not installed"
)
def test_setup_local_certificates_with_mkcert(cert_service, cert_dir):
    """
    Test local certificate setup with mkcert already installed.
    
    This test demonstrates:
    1. Conditional test execution (@pytest.mark.skipif)
    2. Integration testing with real system commands
    3. File existence and permission checks
    4. Multiple assertions for complete verification
    """
    # Attempt to generate real certificates
    cert_service.setup_local_certificates("test.local", cert_dir)
    
    # Verify certificate files were created
    cert_path = cert_dir / "cert.pem"
    key_path = cert_dir / "key.pem"
    assert cert_path.exists(), "Certificate file was not created"
    assert key_path.exists(), "Key file was not created"
    
    # Verify secure permissions were set
    assert oct(cert_path.stat().st_mode)[-3:] == '600', "Incorrect certificate permissions"
    assert oct(key_path.stat().st_mode)[-3:] == '600', "Incorrect key permissions"

@pytest.mark.integration  # Mark as integration test
def test_setup_remote_certificates_letsencrypt(cert_service, cert_dir):
    """
    Test Let's Encrypt certificate setup.
    
    This test demonstrates:
    1. Using test markers (@pytest.mark.integration)
    2. Documenting test requirements
    3. Skipping tests that need special environments
    4. Planning for future implementation
    
    Requirements:
    - Public domain with DNS access
    - Port 80/443 access
    - Root access
    """
    pytest.skip("Integration test requiring public domain and Let's Encrypt access")
    # Implementation notes:
    # 1. Would need CI/CD environment with:
    #    - Test domain
    #    - DNS verification capability
    #    - Port 80/443 access
    # 2. Should use Let's Encrypt staging environment
    # 3. Should clean up certificates after test
