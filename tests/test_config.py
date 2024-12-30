import pytest
from pathlib import Path
import yaml
import tempfile
from ispawn.config import Config
from ispawn.domain.exceptions import ConfigurationError

@pytest.fixture
def temp_config_file():
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yield Path(f.name)
        Path(f.name).unlink()

@pytest.fixture
def sample_config():
    """Sample configuration data."""
    return {
        "name": "test-ispawn",
        "web": {
            "domain": "test.local",
            "subnet": "172.30.0.0/24",
            "mode": "local"
        },
        "services": {
            "rstudio": {
                "port": 8787,
                "enabled": True
            },
            "jupyter": {
                "port": 8888,
                "enabled": True
            }
        }
    }

def test_default_config_creation(temp_config_file):
    """Test creation of default configuration."""
    config = Config(temp_config_file)
    
    assert config.network_name == "ispawn"
    assert config.domain == Config.DEFAULT_DOMAIN
    assert config.subnet == Config.DEFAULT_SUBNET
    assert config.is_local is True

def test_load_existing_config(temp_config_file, sample_config):
    """Test loading existing configuration."""
    # Write sample config
    with open(temp_config_file, 'w') as f:
        yaml.dump(sample_config, f)
    
    config = Config(temp_config_file)
    
    assert config.network_name == "test-ispawn"
    assert config.domain == "test.local"
    assert config.subnet == "172.30.0.0/24"
    assert config.is_local is True

def test_save_config_changes(temp_config_file):
    """Test saving configuration changes."""
    config = Config(temp_config_file)
    
    # Make changes
    config.set_domain("new.local")
    config.set_subnet("172.31.0.0/24")
    config.set_mode("remote")
    
    # Load config again to verify changes were saved
    new_config = Config(temp_config_file)
    assert new_config.domain == "new.local"
    assert new_config.subnet == "172.31.0.0/24"
    assert new_config.is_local is False

def test_service_config_management(temp_config_file):
    """Test service configuration management."""
    config = Config(temp_config_file)
    
    # Get default service config
    rstudio_config = config.get_service_config("rstudio")
    assert rstudio_config["port"] == 8787
    assert rstudio_config["enabled"] is True
    
    # Update service config
    new_config = {
        "port": 8780,
        "enabled": False
    }
    config.update_service_config("rstudio", new_config)
    
    # Verify changes
    updated_config = config.get_service_config("rstudio")
    assert updated_config["port"] == 8780
    assert updated_config["enabled"] is False

def test_invalid_service_config(temp_config_file):
    """Test error handling for invalid service configuration."""
    config = Config(temp_config_file)
    
    with pytest.raises(ConfigurationError):
        config.get_service_config("nonexistent")

def test_invalid_mode_setting(temp_config_file):
    """Test error handling for invalid mode setting."""
    config = Config(temp_config_file)
    
    with pytest.raises(ConfigurationError):
        config.set_mode("invalid")

def test_config_file_permissions(temp_config_file):
    """Test handling of permission errors."""
    config = Config(temp_config_file)
    
    # Make file read-only
    temp_config_file.chmod(0o444)
    
    with pytest.raises(ConfigurationError):
        config.set_domain("new.local")

def test_get_all_config(temp_config_file, sample_config):
    """Test getting complete configuration."""
    with open(temp_config_file, 'w') as f:
        yaml.dump(sample_config, f)
    
    config = Config(temp_config_file)
    all_config = config.get_all()
    
    assert all_config == sample_config
    
    # Verify it's a copy
    all_config["name"] = "modified"
    assert config.network_name == "test-ispawn"

def test_config_directory_creation(temp_config_file):
    """Test configuration directory creation."""
    # Use a path in a non-existent directory
    config_path = temp_config_file.parent / "subdir" / "config.yml"
    
    config = Config(config_path)
    config.set_domain("test.local")  # This should create the directory
    
    assert config_path.exists()
    assert config_path.parent.exists()
    
    # Cleanup
    config_path.unlink()
    config_path.parent.rmdir()

def test_invalid_yaml_handling(temp_config_file):
    """Test handling of invalid YAML content."""
    # Write invalid YAML
    with open(temp_config_file, 'w') as f:
        f.write("invalid: yaml: content:\nindentation")
    
    with pytest.raises(ConfigurationError):
        Config(temp_config_file)
