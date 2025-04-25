import pytest
import uuid

from ispawn.services.image import ImageService
from ispawn.domain.image import ImageConfig
from ispawn.domain.container import Service
from ispawn.domain.exceptions import ImageError


def generate_test_name():
    """Generate a unique test name using UUID."""
    return f"test-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def image_service():
    """Create ImageService instance."""
    return ImageService()


@pytest.fixture
def basic_config():
    """Create a basic image configuration."""
    return ImageConfig(
        base_image="ubuntu:20.04",
        services=[Service.JUPYTER],  # Use Jupyter as it's simpler than RStudio
        name_prefix=f"alpha-{uuid.uuid4().hex[:8]}",
        env_file=None,
        setup_file=None,
    )


def test_build_and_remove_image(image_service, basic_config):
    """Test building and removing an image."""
    try:
        # Get build context and print Dockerfile content
        context = basic_config.get_build_context()
        dockerfile_content = image_service._render_template(
            context["dockerfile"]["template"], context["dockerfile"]["args"]
        )
        print("\n=== Dockerfile Content ===")
        print(dockerfile_content)
        print("=========================\n")

        # Build image
        image = image_service.build_image(basic_config)
        assert image is not None
        assert basic_config.target_image in image.tags

        # Print debug info
        print("\n=== Image Info ===")
        print(f"Expected tag: {basic_config.target_image}")
        print("\nAvailable images:")
        images = image_service.list_images(prefix=basic_config.name_prefix)
        for img in images:
            print(f"  Tags: {img['tags']}")
        print("=================\n")

        # Verify image exists
        assert any(
            basic_config.target_image in img["tags"] for img in images
        ), f"Image with tag {basic_config.target_image} not found in list"

        # Test image info
        image_info = next(
            img for img in images if basic_config.target_image in img["tags"]
        )
        assert "id" in image_info
        assert "size" in image_info
        assert "created" in image_info

    finally:
        # Cleanup
        try:
            image_service.remove_image(basic_config.target_image, force=True)

            # Verify image was removed
            images = image_service.list_images()
            assert not any(
                basic_config.target_image in img["tags"] for img in images
            )
        except ImageError:
            pass  # Ignore cleanup errors


def test_build_nonexistent_image(image_service):
    """Test building from a non-existent base image."""
    config = ImageConfig(
        base_image="nonexistent:latest",
        services=[Service.RSTUDIO],
        name_prefix="ispawn",
        env_file=None,
        setup_file=None,
    )

    with pytest.raises(ImageError, match="Failed to build image"):
        image_service.build_image(config)


def test_remove_nonexistent_image(image_service):
    """Test removing a non-existent image."""
    with pytest.raises(ImageError, match="Image not found"):
        image_service.remove_image("nonexistent:latest")


def test_list_images_with_prefix(image_service):
    """Test listing images with different prefixes."""
    # Create two configs with different prefixes
    config1 = ImageConfig(
        base_image="ubuntu:20.04",
        services=[Service.JUPYTER],
        name_prefix=f"alpha-{uuid.uuid4().hex[:8]}",
        env_file=None,
        setup_file=None,
    )

    config2 = ImageConfig(
        base_image="ubuntu:22.04",
        services=[Service.JUPYTER],
        name_prefix=f"beta-{uuid.uuid4().hex[:8]}",
        env_file=None,
        setup_file=None,
    )

    try:
        # Build both images
        image_service.build_image(config1)
        image_service.build_image(config2)

        # List with first prefix (keep the hyphen)
        prefix1 = config1.name_prefix.split("-", 1)[0] + "-"
        print("\n=== Testing prefix filtering ===")
        print(f"Config1 prefix: {prefix1}")
        print(f"Config1 target: {config1.target_image}")
        print(f"Config2 target: {config2.target_image}")

        images = image_service.list_images(prefix=prefix1)
        print("\nFound images:")
        for img in images:
            print(f"  Tags: {img['tags']}")
        print("===========================\n")
        import docker

        client = docker.from_env()
        imgs = client.images.list()
        for img in imgs:
            tags = img.tags
            print(f"  Tags: {tags}")
        print("===========================\n")

        assert any(config1.target_image in img["tags"] for img in images)
        assert not any(config2.target_image in img["tags"] for img in images)

        # List with second prefix (keep the hyphen)
        prefix2 = config2.name_prefix.split("-", 1)[0] + "-"
        images = image_service.list_images(prefix=prefix2)
        assert not any(config1.target_image in img["tags"] for img in images)
        assert any(config2.target_image in img["tags"] for img in images)

    finally:
        # Cleanup
        try:
            image_service.remove_image(config1.target_image, force=True)
            image_service.remove_image(config2.target_image, force=True)
        except ImageError:
            pass  # Ignore cleanup errors


def test_format_size():
    """Test size formatting."""
    service = ImageService()

    assert service._format_size(100) == "100.0 B"
    assert service._format_size(1024) == "1.0 KB"
    assert service._format_size(1024 * 1024) == "1.0 MB"
    assert service._format_size(1024 * 1024 * 1024) == "1.0 GB"
    assert service._format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"
