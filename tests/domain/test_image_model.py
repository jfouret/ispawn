import pytest
from pathlib import Path
from ispawn.domain.image import ImageConfig
from ispawn.domain.container import Service

@pytest.fixture(params=[
    # Basic configuration
    {
        "base_image": "ubuntu:20.04",
        "services": [Service.RSTUDIO],
        "name_prefix": "ispawn",
        "env_file": None,
        "setup_file": None,
        "templates_dir": None
    },
    # Full configuration with all services
    {
        "base_image": "python:3.9",
        "services": [Service.RSTUDIO, Service.JUPYTER, Service.VSCODE],
        "name_prefix": "custom",
        "env_file": "env_file_path",  # Will be replaced with actual path
        "setup_file": "setup_file_path",  # Will be replaced with actual path
        "templates_dir": None
    },
    # Configuration with string services
    {
        "base_image": "debian:11",
        "services": ["jupyter", "vscode"],
        "name_prefix": "test",
        "env_file": None,
        "setup_file": None,
        "templates_dir": None
    }
])
def valid_args(request, tmp_path):
    """Provide different valid argument configurations."""
    args = request.param
    
    # Create actual files for configurations that need them
    if args["env_file"] is not None:
        env_file = tmp_path / "environment"
        env_file.write_text("TEST_VAR=value")
        args["env_file"] = env_file
    
    if args["setup_file"] is not None:
        setup_file = tmp_path / "setup.sh"
        setup_file.write_text("#!/bin/bash\necho 'setup'")
        args["setup_file"] = setup_file

    if args["templates_dir"] is not None:
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        args["templates_dir"] = templates_dir
    
    return args

@pytest.fixture
def image_config(valid_args):
    """Create an image configuration from valid arguments."""
    return ImageConfig(**valid_args)

def test_image_basic_properties(image_config, valid_args):
    """Test basic image properties are set correctly."""
    assert image_config.base_image == valid_args["base_image"]
    assert len(image_config.services) == len(valid_args["services"])
    assert image_config.name_prefix == valid_args["name_prefix"]
    assert image_config.env_file == valid_args["env_file"]
    assert image_config.setup_file == valid_args["setup_file"]
    assert isinstance(image_config.templates_dir, Path)

def test_target_image_name(image_config, valid_args):
    """Test target image name generation."""
    base_name = valid_args["base_image"].split(':')[0].split('/')[-1]
    tag = valid_args["base_image"].split(':')[1]
    expected = f"{valid_args['name_prefix']}-{base_name}:{tag}"
    assert image_config.target_image == expected

def test_build_args(image_config):
    """Test build arguments generation."""
    args = image_config.get_build_args()
    assert args["BASE_IMAGE"] == image_config.base_image
    assert args["SERVICES"] == ",".join(s.value for s in image_config.services)

def test_context_files(image_config, valid_args):
    """Test context files collection."""
    context_files = image_config.get_context_files()
    
    if valid_args["env_file"]:
        assert "environment" in context_files
        assert context_files["environment"] == valid_args["env_file"]
    
    if valid_args["setup_file"]:
        assert "setup" in context_files
        assert context_files["setup"] == valid_args["setup_file"]

def test_build_context(image_config):
    """Test complete build context generation."""
    context = image_config.get_build_context()
    
    assert context["dockerfile"] == image_config.dockerfile_path
    assert context["entrypoint"] == image_config.entrypoint_path
    assert context["build_args"] == image_config.get_build_args()
    assert context["target_image"] == image_config.target_image
    assert isinstance(context["context_files"], dict)

def test_template_paths(image_config):
    """Test template path resolution."""
    assert image_config.dockerfile_path.name == "Dockerfile.j2"
    assert image_config.entrypoint_path.name == "entrypoint.sh.j2"

@pytest.mark.parametrize("invalid_service", [
    ["invalid_service"],
    ["not_a_service"],
    ["unknown"]
])
def test_invalid_services(invalid_service, valid_args):
    """Test that invalid services raise appropriate errors."""
    invalid_args = valid_args.copy()
    invalid_args["services"] = invalid_service
    
    with pytest.raises(ValueError):
        ImageConfig(**invalid_args)

@pytest.mark.parametrize("registry_image,expected_name", [
    ("docker.io/library/ubuntu:20.04", "ispawn-ubuntu:20.04"),
    ("quay.io/centos/centos:7", "ispawn-centos:7"),
    ("gcr.io/project/image:latest", "ispawn-image:latest")
])
def test_target_image_name_with_registry(registry_image, expected_name):
    """Test target image name generation with various registry paths."""
    config = ImageConfig(
        base_image=registry_image,
        services=[Service.RSTUDIO],
        name_prefix="ispawn",
        env_file=None,
        setup_file=None
    )
    assert config.target_image == expected_name
