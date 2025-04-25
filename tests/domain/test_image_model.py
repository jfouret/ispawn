"""Tests for image configuration."""

import pytest
from ispawn.domain.image import ImageConfig

from ispawn.services.image import ImageService

VALID_CONFIGS = [
    {
        "id": "jupyter_only",
        "params": {
            "base_image": "ubuntu:latest",
            "services": ["jupyter"],
            "name_prefix": "ispawn",
        },
    },
    {
        "id": "multi_service_with_env",
        "params": {
            "base_image": "python:3.9",
            "services": ["jupyter", "vscode"],
            "name_prefix": "ispawn",
            "env_chunk_path": True,
        },
    },
    {
        "id": "rstudio_with_setup",
        "params": {
            "base_image": "debian:bullseye",
            "services": ["rstudio"],
            "name_prefix": "custom",
            "entrypoint_chunk_path": True,
        },
    },
]


@pytest.fixture(params=VALID_CONFIGS)
def valid_config_params(request):
    """Fixture providing valid configuration parameters."""
    return request.param


@pytest.fixture
def mock_files(tmp_path):
    """Create mock files for testing."""
    # Create env file
    env_file = tmp_path / "test.env"
    env_file.write_text("TEST_VAR=value")

    # Create setup file
    setup_file = tmp_path / "setup.sh"
    setup_file.write_text("echo setup")

    build_file = tmp_path / "Dockerfile"
    build_file.write_text("RUN touch /test.txt")

    return {
        "env_chunk_path": env_file,
        "dockerfile_chunk_path": build_file,
        "entrypoint_chunk_path": setup_file,
    }


@pytest.fixture
def valid_image_config(valid_config_params, mock_files):
    """Create a valid ImageConfig instance."""
    params = valid_config_params["params"].copy()

    # Set file paths if specified
    for k in [
        "env_chunk_path",
        "dockerfile_chunk_path",
        "entrypoint_chunk_path",
    ]:
        if k in params and params[k]:
            params[k] = mock_files[k]

    return ImageConfig(**params)


def test_valid_image_config(valid_config_params, valid_image_config):
    """Test valid image configurations."""
    params = valid_config_params["params"]

    # Test basic attributes
    assert valid_image_config.base_image == params["base_image"]
    assert len(valid_image_config.services) == len(params["services"])
    assert valid_image_config.target_image.startswith(
        f"{params['name_prefix']}-{params['base_image']}"
    )

    # Test build context
    context = valid_image_config.get_build_context()

    # Verify template paths
    assert context["Dockerfile"]["template"].exists()
    assert context["entrypoint.sh"]["template"].exists()

    # Verify template arguments
    assert context["Dockerfile"]["args"]["base_image"] == params["base_image"]
    assert isinstance(context["Dockerfile"]["args"]["service_chunks"], str)


def test_build_image(valid_image_config):
    im = ImageService()
    im.build_image(valid_image_config)
    im.remove_image(valid_image_config.target_image)


INVALID_CONFIG_PARAMS = [
    {
        "id": "unknown_service",
        "params": {
            "base_image": "ubuntu:latest",
            "services": ["unknown"],
            "name_prefix": "ispawn",
        },
    },
    {
        "id": "path_do_not_exists",
        "params": {
            "base_image": "python:3.9",
            "services": ["jupyter", "vscode"],
            "name_prefix": "ispawn",
            "env_chunk_path": "/path/to/file/that/does/not/exists",
        },
    },
]


@pytest.fixture(params=INVALID_CONFIG_PARAMS)
def invalid_config_params(request):
    """Fixture providing valid configuration parameters."""
    return request.param


@pytest.fixture
def invalid_image_config(invalid_config_params, mock_files):
    """Create a valid ImageConfig instance."""
    params = invalid_config_params["params"].copy()

    # Set file paths if specified
    for k in [
        "env_chunk_path",
        "dockerfile_chunk_path",
        "entrypoint_chunk_path",
    ]:
        if k in params and params[k]:
            if params[k] is True:
                params[k] = mock_files[k]

    error = False

    try:
        ImageConfig(**params)
    except Exception:
        error = True

    return error


def test_invalid_image_config(invalid_config_params, invalid_image_config):
    """Test valid image configurations."""
    invalid_config_params["params"]
    assert invalid_image_config is True
