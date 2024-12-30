import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from docker.models.images import Image

from ispawn.commands.image import build_image, list_images, remove_images
from ispawn.domain.exceptions import ImageError, ConfigurationError

@pytest.fixture
def mock_image_service():
    """Create mock image service."""
    with patch('ispawn.commands.image.ImageService') as mock_service:
        service_instance = mock_service.return_value
        # Setup default returns
        service_instance.build_image.return_value = Mock(spec=Image)
        service_instance.list_images.return_value = []
        yield service_instance

@pytest.fixture
def mock_args():
    """Create mock command line arguments."""
    args = Mock()
    args.name_prefix = "ispawn"
    args.image = "ubuntu:20.04"
    args.services = "rstudio,jupyter"
    args.env_file = None
    args.setup_file = None
    args.all = False
    args.image_names = []
    return args

def test_build_image_success(mock_image_service, mock_args, capsys):
    """Test successful image build."""
    build_image(mock_args)
    captured = capsys.readouterr()
    
    # Verify service calls
    mock_image_service.build_image.assert_called_once()
    
    # Verify output
    assert "Building image ispawn-ubuntu:20.04" in captured.out
    assert "Successfully built image" in captured.out

def test_build_image_with_files(mock_image_service, mock_args, tmp_path):
    """Test image build with environment and setup files."""
    # Create test files
    env_file = tmp_path / "env"
    setup_file = tmp_path / "setup.sh"
    env_file.touch()
    setup_file.touch()
    
    mock_args.env_file = str(env_file)
    mock_args.setup_file = str(setup_file)
    
    build_image(mock_args)
    
    # Verify builder was created with correct files
    build_call = mock_image_service.build_image.call_args[0][0]
    assert build_call.config.env_file == env_file
    assert build_call.config.setup_file == setup_file

def test_build_image_error(mock_image_service, mock_args, capsys):
    """Test image build error handling."""
    mock_image_service.build_image.side_effect = ImageError("Build failed")
    
    with pytest.raises(SystemExit) as exc_info:
        build_image(mock_args)
    assert exc_info.value.code == 1
    
    captured = capsys.readouterr()
    assert "Error: Build failed" in captured.out

def test_list_images_empty(mock_image_service, mock_args, capsys):
    """Test listing when no images exist."""
    list_images(mock_args)
    captured = capsys.readouterr()
    
    assert "No ispawn images found" in captured.out

def test_list_images_success(mock_image_service, mock_args, capsys):
    """Test successful image listing."""
    mock_image_service.list_images.return_value = [
        {
            "id": "sha256:abc123",
            "tags": ["ispawn-test:latest"],
            "size": "1.2 GB",
            "created": "2023-01-01T00:00:00Z"
        }
    ]
    
    list_images(mock_args)
    captured = capsys.readouterr()
    
    assert "IMAGE ID" in captured.out
    assert "REPOSITORY:TAG" in captured.out
    assert "ispawn-test:latest" in captured.out
    assert "1.2 GB" in captured.out

def test_list_images_error(mock_image_service, mock_args, capsys):
    """Test image listing error handling."""
    mock_image_service.list_images.side_effect = ImageError("Listing failed")
    
    with pytest.raises(SystemExit) as exc_info:
        list_images(mock_args)
    assert exc_info.value.code == 1
    
    captured = capsys.readouterr()
    assert "Error: Listing failed" in captured.out

def test_remove_images_single(mock_image_service, mock_args, capsys):
    """Test removing a single image."""
    mock_args.image_names = ["ispawn-test:latest"]
    
    remove_images(mock_args)
    captured = capsys.readouterr()
    
    mock_image_service.remove_image.assert_called_once_with(
        "ispawn-test:latest",
        force=True
    )
    assert "Removing image ispawn-test:latest" in captured.out
    assert "Image removal completed" in captured.out

def test_remove_images_all(mock_image_service, mock_args, capsys):
    """Test removing all images."""
    mock_args.all = True
    mock_image_service.list_images.return_value = [
        {
            "id": "sha256:abc123",
            "tags": ["ispawn-test1:latest", "ispawn-test1:v1"],
            "size": "1.2 GB",
            "created": "2023-01-01T00:00:00Z"
        },
        {
            "id": "sha256:def456",
            "tags": ["ispawn-test2:latest"],
            "size": "1.0 GB",
            "created": "2023-01-01T00:00:00Z"
        }
    ]
    
    remove_images(mock_args)
    captured = capsys.readouterr()
    
    assert mock_image_service.remove_image.call_count == 3
    assert "Image removal completed" in captured.out

def test_remove_images_error_handling(mock_image_service, mock_args, capsys):
    """Test error handling during image removal."""
    mock_args.image_names = ["image1", "image2"]
    mock_image_service.remove_image.side_effect = [
        ImageError("Remove failed"),
        None
    ]
    
    remove_images(mock_args)
    captured = capsys.readouterr()
    
    assert "Warning: Failed to remove image1" in captured.out
    assert "Image removal completed" in captured.out

def test_remove_images_no_images(mock_image_service, mock_args, capsys):
    """Test remove command with no images specified."""
    remove_images(mock_args)
    captured = capsys.readouterr()
    
    assert "No images specified" in captured.out
    assert not mock_image_service.remove_image.called

def test_remove_images_all_no_images(mock_image_service, mock_args, capsys):
    """Test remove all command when no images exist."""
    mock_args.all = True
    mock_image_service.list_images.return_value = []
    
    remove_images(mock_args)
    captured = capsys.readouterr()
    
    assert "No ispawn images found" in captured.out
    assert not mock_image_service.remove_image.called
