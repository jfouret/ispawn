import pytest
from pathlib import Path
import tempfile
import yaml


@pytest.fixture
def temp_config():
    """Create a temporary ispawn config file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False
    ) as f:
        config = {"name": "ispawn-test", "web": {"domain": "ispawn.test"}}
        yaml.dump(config, f)
        yield Path(f.name)
        Path(f.name).unlink()


@pytest.fixture
def mock_docker_client(mocker):
    """Mock the Docker client for testing."""
    return mocker.patch("docker.from_env")
