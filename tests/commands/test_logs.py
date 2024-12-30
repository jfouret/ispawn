import pytest
from pathlib import Path
import tempfile
import yaml
import os
from unittest.mock import Mock, patch

from ispawn.config import Config
from ispawn.commands.logs import logs_command

@pytest.fixture
def temp_config():
    """Create temporary configuration for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "ispawn"
        config_dir.mkdir()
        config_file = config_dir / "config.yml"
        
        # Create test configuration
        config = {
            "name": "ispawn-test",
            "web": {
                "domain": "test.localhost",
                "subnet": "172.30.0.0/24",
                "mode": "local"
            },
            "logs": {
                "dir": str(config_dir / "logs")
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        yield Config(config_file)

def test_logs_command_container_not_found(temp_config):
    """Test logs command when container doesn't exist."""
    with patch('ispawn.commands.logs.DockerService') as mock_docker:
        mock_docker.return_value.get_container.return_value = None
        
        with pytest.raises(RuntimeError, match="Container test not found"):
            logs_command(temp_config, "test")

def test_logs_command_no_logs(temp_config):
    """Test logs command when no logs exist."""
    with patch('ispawn.commands.logs.DockerService') as mock_docker:
        mock_container = Mock()
        mock_docker.return_value.get_container.return_value = mock_container
        
        with pytest.raises(RuntimeError, match="No logs found for container test"):
            logs_command(temp_config, "test")

def test_logs_command_with_logs(temp_config, capsys):
    """Test logs command with existing logs."""
    # Create test log directory and files
    container_name = "test"
    log_dir = temp_config.log_dir / f"{container_name}.1"
    log_dir.mkdir(parents=True)
    
    # Create entrypoint log
    entrypoint_log = log_dir / "entrypoint.log"
    entrypoint_log.write_text("Entrypoint started\n")
    
    # Create service log directory and file
    jupyter_dir = log_dir / "jupyter"
    jupyter_dir.mkdir()
    jupyter_log = jupyter_dir / "jupyter.log"
    jupyter_log.write_text("Jupyter started\n")
    
    # Mock Docker container
    with patch('ispawn.commands.logs.DockerService') as mock_docker:
        mock_container = Mock()
        mock_container.logs.return_value = b"Docker logs\n"
        mock_docker.return_value.get_container.return_value = mock_container
        
        # Run logs command
        logs_command(temp_config, container_name)
        
        # Check output
        captured = capsys.readouterr()
        assert "=== Docker Container Logs ===" in captured.out
        assert "Docker logs" in captured.out
        assert "=== Service Logs ===" in captured.out
        assert "Entrypoint started" in captured.out
        assert "Jupyter started" in captured.out

def test_logs_command_follow_mode(temp_config):
    """Test logs command in follow mode."""
    # Create test log directory and files
    container_name = "test"
    log_dir = temp_config.log_dir / f"{container_name}.1"
    log_dir.mkdir(parents=True)
    
    # Create entrypoint log
    entrypoint_log = log_dir / "entrypoint.log"
    entrypoint_log.write_text("Entrypoint started\n")
    
    # Mock Docker container and os.system
    with patch('ispawn.commands.logs.DockerService') as mock_docker, \
         patch('ispawn.commands.logs.os.system') as mock_system:
        mock_container = Mock()
        mock_container.logs.return_value = b"Docker logs\n"
        mock_docker.return_value.get_container.return_value = mock_container
        
        # Run logs command in follow mode
        logs_command(temp_config, container_name, follow=True)
        
        # Verify tail -f was called
        mock_system.assert_called_with(f"tail -f {entrypoint_log}")

def test_logs_command_multiple_log_dirs(temp_config, capsys):
    """Test logs command with multiple log directories."""
    # Create multiple test log directories
    container_name = "test"
    for i in range(1, 4):
        log_dir = temp_config.log_dir / f"{container_name}.{i}"
        log_dir.mkdir(parents=True)
        
        # Create entrypoint log with different content
        entrypoint_log = log_dir / "entrypoint.log"
        entrypoint_log.write_text(f"Entrypoint log {i}\n")
    
    # Mock Docker container
    with patch('ispawn.commands.logs.DockerService') as mock_docker:
        mock_container = Mock()
        mock_container.logs.return_value = b"Docker logs\n"
        mock_docker.return_value.get_container.return_value = mock_container
        
        # Run logs command
        logs_command(temp_config, container_name)
        
        # Check that we got the latest log
        captured = capsys.readouterr()
        assert "Entrypoint log 3" in captured.out
