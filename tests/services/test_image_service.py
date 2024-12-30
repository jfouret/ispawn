import pytest
from unittest.mock import Mock, patch, mock_open, ANY
import docker
from pathlib import Path
import tempfile
import os

from ispawn.services.image import ImageService
from ispawn.domain.image import ImageBuilder, ImageConfig
from ispawn.domain.container import Service
from ispawn.domain.exceptions import ImageError

@pytest.fixture
def mock_docker_client():
    """Create a mock Docker client."""
    with patch('docker.from_env') as mock_client:
        mock_client.return_value.images = Mock()
        yield mock_client.return_value

@pytest.fixture
def image_service(mock_docker_client):
    """Create ImageService instance with mocked Docker client."""
    return ImageService()

@pytest.fixture
def basic_config():
    """Create a basic image configuration."""
    return ImageConfig(
        base_image="ubuntu:20.04",
        services=[Service.RSTUDIO, Service.JUPYTER]
    )

@pytest.fixture
def image_builder(basic_config):
    """Create ImageBuilder instance."""
    return ImageBuilder(basic_config)

@pytest.fixture
def mock_templates(tmp_path):
    """Create mock template files."""
    dockerfile = tmp_path / "Dockerfile.j2"
    entrypoint = tmp_path / "entrypoint.sh.j2"
    
    dockerfile.write_text("FROM {{ BASE_IMAGE }}\nSERVICES={{ SERVICES }}")
    entrypoint.write_text("#!/bin/bash\necho {{ SERVICES }}")
    
    return {"dockerfile": dockerfile, "entrypoint": entrypoint}

def test_build_image_success(image_service, image_builder, mock_docker_client, mock_templates):
    """Test successful image build."""
    # Setup mock image
    mock_image = Mock()
    mock_docker_client.images.build.return_value = (mock_image, [])
    
    # Mock template paths
    with patch.object(image_builder, 'get_dockerfile_path') as mock_dockerfile_path:
        with patch.object(image_builder, 'get_entrypoint_path') as mock_entrypoint_path:
            mock_dockerfile_path.return_value = mock_templates["dockerfile"]
            mock_entrypoint_path.return_value = mock_templates["entrypoint"]
            
            # Build image
            result = image_service.build_image(image_builder)
            
            # Verify build was called with correct arguments
            mock_docker_client.images.build.assert_called_once()
            build_args = mock_docker_client.images.build.call_args[1]
            assert build_args["tag"] == image_builder.config.target_image
            assert build_args["rm"] is True
            assert "buildargs" in build_args
            
            assert result == mock_image

def test_build_image_error(image_service, image_builder, mock_docker_client, mock_templates):
    """Test image build error handling."""
    mock_docker_client.images.build.side_effect = docker.errors.BuildError("Build failed", "")
    
    with patch.object(image_builder, 'get_dockerfile_path') as mock_dockerfile_path:
        with patch.object(image_builder, 'get_entrypoint_path') as mock_entrypoint_path:
            mock_dockerfile_path.return_value = mock_templates["dockerfile"]
            mock_entrypoint_path.return_value = mock_templates["entrypoint"]
            
            with pytest.raises(ImageError, match="Failed to build image"):
                image_service.build_image(image_builder)

def test_list_images(image_service, mock_docker_client):
    """Test listing images."""
    # Setup mock images
    mock_image = Mock()
    mock_image.short_id = "abc123"
    mock_image.tags = ["ispawn-test:latest"]
    mock_image.attrs = {
        "Size": 1024 * 1024 * 100,  # 100MB
        "Created": "2023-01-01T00:00:00Z"
    }
    mock_docker_client.images.list.return_value = [mock_image]
    
    images = image_service.list_images()
    
    assert len(images) == 1
    assert images[0]["id"] == "abc123"
    assert images[0]["tags"] == ["ispawn-test:latest"]
    assert images[0]["size"] == "100.0 MB"
    assert images[0]["created"] == "2023-01-01T00:00:00Z"

def test_list_images_error(image_service, mock_docker_client):
    """Test error handling when listing images."""
    mock_docker_client.images.list.side_effect = docker.errors.APIError("API error")
    
    with pytest.raises(ImageError, match="Failed to list images"):
        image_service.list_images()

def test_remove_image(image_service, mock_docker_client):
    """Test image removal."""
    image_service.remove_image("ispawn-test:latest")
    
    mock_docker_client.images.remove.assert_called_once_with(
        "ispawn-test:latest",
        force=False
    )

def test_remove_image_not_found(image_service, mock_docker_client):
    """Test error handling when removing non-existent image."""
    mock_docker_client.images.remove.side_effect = docker.errors.ImageNotFound("not found")
    
    with pytest.raises(ImageError, match="Image not found"):
        image_service.remove_image("nonexistent:latest")

def test_remove_image_error(image_service, mock_docker_client):
    """Test error handling when image removal fails."""
    mock_docker_client.images.remove.side_effect = docker.errors.APIError("API error")
    
    with pytest.raises(ImageError, match="Failed to remove image"):
        image_service.remove_image("test:latest")

def test_format_size():
    """Test size formatting."""
    service = ImageService()
    
    assert service._format_size(100) == "100.0 B"
    assert service._format_size(1024) == "1.0 KB"
    assert service._format_size(1024 * 1024) == "1.0 MB"
    assert service._format_size(1024 * 1024 * 1024) == "1.0 GB"
    assert service._format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"

@pytest.mark.integration
class TestImageServiceIntegration:
    """Integration tests that require a running Docker daemon."""
    
    @pytest.fixture
    def image_service_real(self):
        """Create a real ImageService instance."""
        return ImageService()
    
    def test_build_and_remove_image(self, image_service_real, basic_config, tmp_path):
        """Test building and removing an image."""
        builder = ImageBuilder(basic_config)
        
        try:
            # Build image
            image = image_service_real.build_image(builder)
            assert image is not None
            
            # Verify image exists
            images = image_service_real.list_images()
            assert any(basic_config.target_image in img["tags"] for img in images)
            
        finally:
            # Cleanup
            try:
                image_service_real.remove_image(basic_config.target_image, force=True)
            except ImageError:
                pass  # Ignore cleanup errors
