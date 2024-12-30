import sys
from pathlib import Path
from typing import Optional

from ispawn.domain.image import ImageConfig, ImageBuilder
from ispawn.services.image import ImageService
from ispawn.domain.exceptions import ImageError, ConfigurationError
from ispawn.domain.container import Service

def build_image(args) -> None:
    """Build a Docker image with specified services."""
    try:
        # Parse services
        services = args.services.split(',')
        services = [s.strip() for s in services]

        # Create image configuration
        config = ImageConfig(
            base_image=args.image,
            services=services,
            name_prefix=args.name_prefix,
            env_file=Path(args.env_file) if args.env_file else None,
            setup_file=Path(args.setup_file) if args.setup_file else None
        )

        # Create builder and service
        builder = ImageBuilder(config)
        service = ImageService()

        print(f"Building image {config.target_image}...")
        print(f"Base image: {config.base_image}")
        print(f"Services: {', '.join(s.value for s in config.services)}")

        # Build image
        image = service.build_image(builder)
        print(f"Successfully built image: {config.target_image}")

    except (ImageError, ConfigurationError) as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

def list_images(args) -> None:
    """List all ispawn images."""
    try:
        service = ImageService()
        images = service.list_images(prefix=args.name_prefix)

        if not images:
            print("No ispawn images found.")
            return

        # Print header
        print(f"{'IMAGE ID':<12} {'REPOSITORY:TAG':<50} {'SIZE':<10} {'CREATED':<30}")
        print("-" * 100)

        # Print images
        for image in images:
            for tag in image["tags"]:
                print(
                    f"{image['id'][7:19]:<12} "
                    f"{tag:<50} "
                    f"{image['size']:<10} "
                    f"{image['created'][:19]:<30}"
                )

    except ImageError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

def remove_images(args) -> None:
    """Remove one or more ispawn images."""
    try:
        service = ImageService()

        if args.all:
            # Remove all ispawn images
            images = service.list_images(prefix=args.name_prefix)
            if not images:
                print("No ispawn images found.")
                return

            for image in images:
                for tag in image["tags"]:
                    try:
                        print(f"Removing image {tag}...")
                        service.remove_image(tag, force=True)
                    except ImageError as e:
                        print(f"Warning: Failed to remove {tag}: {str(e)}")

        else:
            # Remove specific images
            if not args.image_names:
                print("No images specified.")
                return

            for name in args.image_names:
                try:
                    print(f"Removing image {name}...")
                    service.remove_image(name, force=True)
                except ImageError as e:
                    print(f"Warning: Failed to remove {name}: {str(e)}")

        print("Image removal completed.")

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)
