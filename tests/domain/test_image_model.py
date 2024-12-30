import pytest
from pathlib import Path
from ispawn.domain.image import ImageConfig, ImageBuilder
from ispawn.domain.container import Service
from ispawn.domain.exceptions import ValidationError

@pytest.fixture
def basic_config():
    """Create a basic image configuration."""
    return ImageConfig(
        base_image="ubuntu:20.04",
        services=[Service.RSTUDIO, Service.JUPYTER]
    )

@pytest.fixture
def full_config(tmp_path):
    """Create a full image configuration with all options."""
    env_file = tmp_path / "environment"
    setup_file = tmp_path / "setup.sh"
    
    # Create test files
    env_file.write_text("TEST_VAR=value")
    setup_file.write_text("#!/bin/bash\necho 'setup'")
    
    return ImageConfig(
        base_image="ubuntu:20.04",
        services=[Service.RSTUDIO, Service.JUPYTER],
        name_prefix="custom",
        env_file=env_file,
        setup_file=setup_file
    )

def test_image_config_basic(basic_config):
    """Test basic image configuration."""
    assert basic_config.base_image == "ubuntu:20.04"
    assert len(basic_config.services) == 2
    assert Service.RSTUDIO in basic_config.services
    assert Service.JUPYTER in basic_config.services
    assert basic_config.name_prefix == "ispawn"
    assert basic_config.env_file is None
    assert basic_config.setup_file is None

def test_image_config_full(full_config):
    """Test full image configuration with all options."""
    assert full_config.base_image == "ubuntu:20.04"
    assert len(full_config.services) == 2
    assert full_config.name_prefix == "custom"
    assert full_config.env_file.exists()
    assert full_config.setup_file.exists()

def test_image_config_string_services():
    """Test image configuration with string service names."""
    config = ImageConfig(
        base_image="ubuntu:20.04",
        services=["rstudio", "jupyter"]
    )
    
    assert isinstance(config.services[0], Service)
    assert config.services[0] == Service.RSTUDIO
    assert config.services[1] == Service.JUPYTER

def test_image_config_invalid_service():
    """Test image configuration with invalid service."""
    with pytest.raises(ValueError):
        ImageConfig(
            base_image="ubuntu:20.04",
            services=["invalid"]
        )

def test_target_image_name_simple():
    """Test target image name generation for simple base image."""
    config = ImageConfig(
        base_image="ubuntu:20.04",
        services=[Service.RSTUDIO]
    )
    
    assert config.target_image == "ispawn-ubuntu:20.04"

def test_target_image_name_registry():
    """Test target image name generation for registry image."""
    config = ImageConfig(
        base_image="docker.io/library/ubuntu:20.04",
        services=[Service.RSTUDIO]
    )
    
    assert config.target_image == "ispawn-ubuntu:20.04"

def test_target_image_name_custom_prefix():
    """Test target image name generation with custom prefix."""
    config = ImageConfig(
        base_image="ubuntu:20.04",
        services=[Service.RSTUDIO],
        name_prefix="custom"
    )
    
    assert config.target_image == "custom-ubuntu:20.04"

def test_build_args():
    """Test build arguments generation."""
    config = ImageConfig(
        base_image="ubuntu:20.04",
        services=[Service.RSTUDIO, Service.JUPYTER]
    )
    
    args = config.get_build_args()
    assert args["BASE_IMAGE"] == "ubuntu:20.04"
    assert args["SERVICES"] == "rstudio,jupyter"

def test_image_builder_paths(basic_config):
    """Test image builder path resolution."""
    builder = ImageBuilder(basic_config)
    
    assert builder.get_dockerfile_path().name == "Dockerfile.j2"
    assert builder.get_entrypoint_path().name == "entrypoint.sh.j2"

def test_image_builder_context_files(full_config):
    """Test image builder context files collection."""
    builder = ImageBuilder(full_config)
    context_files = builder.get_context_files()
    
    assert "environment" in context_files
    assert "setup" in context_files
    assert context_files["environment"] == full_config.env_file
    assert context_files["setup"] == full_config.setup_file

def test_image_builder_context_files_missing(basic_config, tmp_path):
    """Test image builder handles missing context files."""
    basic_config.env_file = tmp_path / "nonexistent"
    basic_config.setup_file = tmp_path / "also-nonexistent"
    
    builder = ImageBuilder(basic_config)
    context_files = builder.get_context_files()
    
    assert not context_files

def test_image_builder_build_context(full_config):
    """Test complete build context generation."""
    builder = ImageBuilder(full_config)
    context = builder.get_build_context()
    
    assert "dockerfile" in context
    assert "entrypoint" in context
    assert "context_files" in context
    assert "build_args" in context
    assert "target_image" in context
    
    assert context["build_args"]["BASE_IMAGE"] == full_config.base_image
    assert context["target_image"] == full_config.target_image
    assert len(context["context_files"]) == 2
