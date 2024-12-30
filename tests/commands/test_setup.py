import pytest
from pathlib import Path
import tempfile
import yaml
import os
from unittest.mock import Mock, patch

from ispawn.config import Config, Mode, CertMode
from ispawn.commands.setup import (
    setup_command, setup_traefik, setup_logs, 
    setup_certificates, render_template
)
from ispawn.domain.exceptions import ConfigurationError, CertificateError

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock()
    config.network_name = "ispawn-test"
    config.domain = "test.localhost"
    config.subnet = "172.30.0.0/24"
    config.mode = Mode.LOCAL
    config.cert_mode = CertMode.PROVIDED
    config.email = None
    config.cert_dir = Path("/tmp/certs")
    config.log_dir = Path("/tmp/logs")
    config.config_dir = Path("/tmp/config")
    return config

@pytest.fixture
def mock_docker_service():
    """Create a mock Docker service."""
    service = Mock()
    service.ensure_network.return_value = None
    return service

@pytest.fixture
def mock_cert_service():
    """Create a mock certificate service."""
    service = Mock()
    service.setup_local_certificates.return_value = None
    service.setup_remote_certificates.return_value = None
    service.validate_certificates.return_value = None
    return service

def test_render_template(tmp_path):
    """Test template rendering."""
    # Create test template
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_path = template_dir / "test.j2"
    template_path.write_text("Hello {{ name }}!")
    
    # Create output path
    output_path = tmp_path / "output.txt"
    
    # Render template
    render_template(template_path, output_path, {"name": "World"})
    
    # Verify output
    assert output_path.exists()
    assert output_path.read_text() == "Hello World!"

def test_setup_traefik(mock_config):
    """Test Traefik setup."""
    with patch('ispawn.commands.setup.render_template') as mock_render:
        setup_traefik(mock_config)
        
        # Verify template was rendered
        mock_render.assert_called_once()
        _, _, context = mock_render.call_args[0]
        assert context["network_name"] == mock_config.network_name
        assert context["domain"] == mock_config.domain
        assert context["mode"] == mock_config.mode.value
        assert context["cert_mode"] == mock_config.cert_mode.value

def test_setup_logs(mock_config, tmp_path):
    """Test log directory setup."""
    mock_config.log_dir = tmp_path / "logs"
    setup_logs(mock_config)
    
    # Verify directory was created
    assert mock_config.log_dir.exists()
    assert mock_config.log_dir.is_dir()
    
    # Verify permissions
    assert oct(mock_config.log_dir.stat().st_mode)[-3:] == '700'
    
    # Verify README
    readme = mock_config.log_dir / "README.md"
    assert readme.exists()
    assert "ispawn Logs Directory" in readme.read_text()

def test_setup_certificates_local(mock_config, mock_cert_service):
    """Test local certificate setup."""
    mock_config.mode = Mode.LOCAL
    setup_certificates(mock_config, mock_cert_service)
    mock_cert_service.setup_local_certificates.assert_called_once_with(
        mock_config.domain, mock_config.cert_dir
    )

def test_setup_certificates_remote_provided(mock_config, mock_cert_service):
    """Test remote certificate setup with provided certificates."""
    mock_config.mode = Mode.REMOTE
    mock_config.cert_mode = CertMode.PROVIDED
    setup_certificates(mock_config, mock_cert_service)
    mock_cert_service.validate_certificates.assert_called_once_with(mock_config.cert_dir)

def test_setup_certificates_remote_letsencrypt(mock_config, mock_cert_service):
    """Test remote certificate setup with Let's Encrypt."""
    mock_config.mode = Mode.REMOTE
    mock_config.cert_mode = CertMode.LETSENCRYPT
    mock_config.email = "test@example.com"
    setup_certificates(mock_config, mock_cert_service)
    mock_cert_service.setup_remote_certificates.assert_called_once_with(
        mock_config.cert_dir, mock_config.email
    )

def test_setup_certificates_remote_letsencrypt_no_email(mock_config, mock_cert_service):
    """Test remote certificate setup with Let's Encrypt but no email."""
    mock_config.mode = Mode.REMOTE
    mock_config.cert_mode = CertMode.LETSENCRYPT
    mock_config.email = None
    with pytest.raises(CertificateError, match="Email is required"):
        setup_certificates(mock_config, mock_cert_service)

@patch('ispawn.commands.setup.DockerService')
@patch('ispawn.commands.setup.CertificateService')
def test_setup_command_local(mock_cert_service_class, mock_docker_service_class, mock_config):
    """Test setup command in local mode."""
    # Setup mocks
    mock_docker_service = Mock()
    mock_cert_service = Mock()
    mock_docker_service_class.return_value = mock_docker_service
    mock_cert_service_class.return_value = mock_cert_service
    
    # Run setup
    setup_command(mock_config)
    
    # Verify services were used
    mock_docker_service.ensure_network.assert_called_once_with(
        mock_config.network_name, mock_config.subnet
    )
    mock_cert_service.setup_local_certificates.assert_called_once()

@patch('ispawn.commands.setup.DockerService')
@patch('ispawn.commands.setup.CertificateService')
def test_setup_command_error(mock_cert_service_class, mock_docker_service_class, mock_config):
    """Test setup command error handling."""
    mock_docker_service = Mock()
    mock_docker_service.ensure_network.side_effect = Exception("Network error")
    mock_docker_service_class.return_value = mock_docker_service
    
    with pytest.raises(RuntimeError, match="Setup failed: Network error"):
        setup_command(mock_config)

def test_setup_command_invalid_mode(mock_config):
    """Test setup command with invalid mode."""
    with pytest.raises(ConfigurationError):
        setup_command(mock_config, mode="invalid")

def test_setup_command_invalid_cert_mode(mock_config):
    """Test setup command with invalid certificate mode."""
    with pytest.raises(ConfigurationError):
        setup_command(mock_config, cert_mode="invalid")
