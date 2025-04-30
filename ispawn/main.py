import click
from pathlib import Path
from typing import List
import sys
from tabulate import tabulate

from ispawn.domain.config import InstallMode, CertMode, ProxyMode, Config
from ispawn.services.config import ConfigManager
from ispawn.domain.image import Service, ImageConfig
from ispawn.services.image import ImageService
from ispawn.services.container import ContainerService
from ispawn.domain.container import ContainerConfig

import re


def is_valid_path(path):
    return bool(re.match(r"^/[a-zA-Z0-9\-_\. /]+$", path)) and "//" not in path


def parse_volumes(volumes, mnt):
    results = []
    for volume in volumes:
        if ":" in volume:
            parsed = volume.split(":")
            if len(parsed) > 3:
                raise ValueError(f"Volume {volume} is not valid")
            if len(parsed) == 3:
                if parsed[2] not in ["ro", "rw"]:
                    raise ValueError(f"Volume {volume} is not valid")
            results.append(parsed)
        else:
            p1 = mnt.rstrip("/")
            p2 = volume.lstrip("/").rstrip("/")
            results.append([f"{volume}", f"{p1}/{p2}"])
    for volume in results:
        # test the the first exists and make it absolute
        volume[0] = str(Path(volume[0]).resolve(strict=True))
        # test that the second is a possible path (no forbidden chars)
        if not is_valid_path(volume[1]):
            raise ValueError(f"Volume {volume[1]} is not valid")
    return results


@click.group()
@click.option(
    "-f",
    "--force",
    default=False,
    is_flag=True,
    help="Force overwrite of existing configurations or resources.",
)
@click.option(
    "-u",
    "--user",
    default=False,
    is_flag=True,
    help=(
        "Prioritize user-level configuration (~/.ispawn) "
        "over system-level configuration (/etc/ispawn)."
    ),
)
@click.pass_context
def cli(ctx, force, user):
    """
    ispawn: A tool to manage containerized development environments.

    Provides commands to set up the environment, build images, and run/manage
    containers with services like VSCode, RStudio, and Jupyter.
    """
    ctx.obj = {"force": force, "user": user}
    config = Config.load(user_mode=user)
    if config is None:
        config = Config.load(user_mode=(not user))
    if config is not None:
        ctx.obj["config"] = config
    if "config" not in ctx.obj.keys() and ctx.invoked_subcommand != "setup":
        click.echo(
            click.style(
                "Error: No valid config found, run ispawn setup", fg="red"
            ),
            err=True,
        )
        print(ctx.obj)
        sys.exit(1)


@cli.command()
@click.option(
    "-n",
    "--name",
    default="ispawn",
    help=(
        "Namespace prefix for Docker objects (networks, volumes)."
        " Default: 'ispawn'."
    ),
)
@click.option(
    "-m",
    "--mode",
    default=ProxyMode.LOCAL.value,
    type=click.Choice([m.value for m in ProxyMode]),
    help="Proxy mode: 'local' for development access only,"
    "'remote' for external access. Default: 'local'.",
)
@click.option(
    "-d",
    "--domain",
    default="ispawn.localhost",
    help="Base domain name for accessing services. Default: "
    "'ispawn.localhost'.",
)
@click.option(
    "--install-mode",
    default=InstallMode.USER.value,
    type=click.Choice([m.value for m in InstallMode]),
    help="Installation scope: 'user' (~/.ispawn) or 'system' (/etc/ispawn)."
    "Default: 'user'.",
)
@click.option(
    "--subnet",
    default="172.30.0.0/24",
    help="CIDR notation for the Docker network subnet. Default: "
    "'172.30.0.0/24'.",
)
@click.option(
    "--user-in-namespace",
    is_flag=True,
    help="If set, include the username in the container namespace "
    "(e.g., 'username-containername').",
)
@click.option(
    "--cert-mode",
    type=click.Choice([m.value for m in CertMode]),
    help="Certificate mode for 'remote' proxy mode: 'letsencrypt' for "
    "automatic certs or 'provided' for custom certs.",
)
@click.option(
    "--cert-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Directory containing 'cert.pem' and 'key.pem' when using 'provided' "
    "cert-mode.",
)
@click.option(
    "--email",
    help="Email address required for Let's Encrypt certificate generation.",
)
@click.option(
    "-v",
    "--volume",
    "volumes",
    help=(
        "Define default volumes to mount in all containers. Format: "
        "'host_path:container_path[:ro]'. "
        "If only 'host_path' is given, it mounts to '/mnt/host_path_basename'."
    ),
    multiple=True,
)
@click.option(
    "--mount-point",
    help="Default base directory inside containers for volumes specified"
    " without a target path. Default: '/mnt'.",
    default="/mnt",
)
@click.option(
    "--dns",
    default=["8.8.8.8", "8.8.4.4"],
    multiple=True,
    help="DNS servers to use within containers. Can be specified multiple "
    "times. Defaults: 8.8.8.8, 8.8.4.4.",
)
@click.option(
    "--env-chunk-path",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="Path to a file containing environment variables (one per line) to"
    "inject into built images.",
)
@click.option(
    "--dockerfile-chunk-path",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="Path to a file containing Dockerfile instructions to append during"
    "image builds.",
)
@click.option(
    "--entrypoint-chunk-path",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="Path to a script to prepend to the container's entrypoint.",
)
@click.option(
    "--home-prefix",
    default="/home/",
    help="Prefix for user home directories inside the container. Default: "
    "'/home/'.",
)
@click.option(
    "--timezone",
    default="Europe/Paris",
    help="Timezone to set within containers (e.g., 'America/New_York')."
    " Default: 'Europe/Paris'.",
)
@click.pass_context
def setup(ctx, **kwargs):
    """
    Initialize the ispawn environment.

    Sets up the necessary configurations, including the Traefik reverse proxy,
    Docker network, default volumes, and build customization settings.
    This command only needs to be run once unless configuration changes are
    needed.
    """
    kwargs["dns"] = [ip for ip in kwargs["dns"]]
    kwargs["volumes"] = parse_volumes(kwargs["volumes"], kwargs["mount_point"])
    config = Config(**kwargs)
    config_manager = ConfigManager(config, ctx.obj["force"])
    config_manager.apply_config()


@cli.command(name="build")
@click.option(
    "-b",
    "--base",
    required=True,
    help="The base Docker image tag to use for building (e.g., "
    "'ubuntu:22.04').",
)
@click.option(
    "-s",
    "--service",
    "services",
    multiple=True,
    type=click.Choice([s.value for s in Service], case_sensitive=False),
    help=(
        "Specify services to include in the image. Can be used multiple times. "
        "Available: " + ", ".join([s.value for s in Service]) + ". "
        "Defaults to rstudio and jupyterhub if none are specified."
    ),
)
@click.pass_context
def build(ctx, **kwargs):
    """
    Build a custom Docker image with specified services.

    Constructs a Docker image based on the provided base image, incorporating
    selected services and applying any global build customizations defined
    during 'ispawn setup'.
    """
    # Set default services if none specified
    if "services" not in kwargs.keys():
        kwargs["services"] = []
    if len(kwargs["services"]) == 0:
        kwargs["services"] = ["rstudio", "jupyterhub"]
    kwargs["config"] = ctx.obj["config"]
    image_config = ImageConfig(**kwargs)
    im = ImageService(ctx.obj["config"])
    im.build_image(image_config)


@cli.group()
def image():
    """Commands for managing ispawn Docker images."""
    pass


@image.command(name="list")
@click.pass_context
def list_cmd(ctx):
    """List ispawn-related Docker images."""
    im = ImageService(ctx.obj["config"])
    images = im.list_images()
    table = tabulate(
        [
            [
                image["id"],
                " ".join(image["tags"]),
                image["size"],
                image["created"].split(".")[0].replace("T", " "),
            ]
            for image in images
        ],
        headers=["ID", "TAGS", "SIZE", "CREATED (YYYY-MM-DD)"],
    )
    click.echo(table)


@image.command(name="remove")
@click.argument("images", nargs=-1, metavar="IMAGE_ID_OR_TAG")
@click.option(
    "--all", is_flag=True, help="Remove all ispawn-related Docker images."
)
@click.pass_context
def remove(ctx, images: List[str], all: bool):
    """
    Remove one or more ispawn Docker images.

    You can specify images by their ID or tag.
    """
    im = ImageService(ctx.obj["config"])
    for digest in images:
        im.remove_image(digest, force=ctx.obj["force"])
    if all:
        for image in im.list_images():
            im.remove_image(image["id"], force=ctx.obj["force"])


@cli.command()
@click.option(
    "-n", "--name", required=True, help="Unique name for the container."
)
@click.option(
    "-b",
    "--base",
    required=True,
    help="Base Docker image tag to use (e.g., 'ubuntu:22.04').",
)
@click.option(
    "--build",
    is_flag=True,
    help="Build the required image automatically if it doesn't exist.",
)
@click.option(
    "-s",
    "--service",
    "services",
    multiple=True,
    type=click.Choice([s.value for s in Service], case_sensitive=False),
    help=(
        "Specify services to run in the container. Can be used multiple times. "
        "Available: " + ", ".join([s.value for s in Service]) + ". "
        "Defaults to vscode, rstudio, jupyter if none are specified."
    ),
)
@click.option(
    "-v",
    "--volume",
    "volumes",
    multiple=True,
    help=(
        "Mount a host directory into the container. "
        "Format: 'host_path:container_path[:ro]'. Can be used multiple times."
    ),
)
@click.option(
    "-g",
    "--group",
    help=(
        "Restrict RStudio access to users belonging to this group. "
        "Defaults to the primary group of the specified user."
    ),
)
@click.option(
    "--user",
    help=(
        "Username or UID to run the container processes as. "
        "Defaults to the current user."
    ),
)
@click.option(
    "--no-sudo",
    is_flag=True,
    help="Disable sudo privileges for the user inside the container.",
)
@click.pass_context
def run(
    ctx,
    name,
    base: str,
    services: List[str],
    volumes: List[str],
    build,
    group: str,
    user: str,
    no_sudo: bool,
):
    """
    Create and run a new development container.

    Launches a container based on the specified image, running the selected
    services (VSCode, RStudio, Jupyter by default). Configures networking,
    volumes, and user access according to options and global settings.
    """
    try:
        # Parse volumes
        parsed_volumes = parse_volumes(volumes, ctx.obj["config"].mount_point)

        # Set default services if none specified
        if not services:
            services = []
        if len(services) == 0:
            services = ["vscode", "rstudio", "jupyter"]

        # Create image config
        image_config = ImageConfig(
            base=base,
            services=[Service(s) for s in services],
            config=ctx.obj["config"],
        )

        im = ImageService(ctx.obj["config"])
        if not im.check_image(image_config):
            if build:
                im.build_image(image_config)
            else:
                print(
                    f"Image {image_config.target_image} not found. "
                    "Use build command or --build to build it."
                )
                sys.exit(1)

        # Create container config
        container_config = ContainerConfig(
            name=name,
            config=ctx.obj["config"],
            image_config=image_config,
            volumes=parsed_volumes,
            group=group,
            user=user,
            sudo=not no_sudo,
        )

        # Initialize container service
        container_service = ContainerService(ctx.obj["config"])

        # Run container
        container = container_service.run_container(
            container_config, force=ctx.obj["force"]
        )
        click.echo(f"Container {container.name} started successfully")

        # Display service URLs
        click.echo("\nService URLs:")
        for service in container_config.image_config.services:
            domain = container_config.get_service_domain(service)
            click.echo(f"{service.value}: https://{domain}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="list")
@click.pass_context
def list_containers(ctx):
    """List currently running ispawn containers."""
    try:
        container_service = ContainerService(ctx.obj["config"])
        containers = container_service.list_containers()
        if not containers:
            click.echo("No containers found")
            return
        table = tabulate(
            [
                [
                    container["name"],
                    container["id"],
                    container["status"],
                    container["image"],
                ]
                for container in containers
            ],
            headers=["NAME", "ID", "STATUS", "IMAGE"],
        )
        click.echo(table)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="stop")
@click.argument("containers", nargs=-1, metavar="CONTAINER_NAME_OR_ID")
@click.option("--all", is_flag=True, help="Stop all running ispawn containers.")
@click.option(
    "--remove",
    is_flag=True,
    help="Remove the container(s) after stopping them.",
)
@click.pass_context
def stop(ctx, containers, all, remove):
    """
    Stop one or more running ispawn containers.

    You can specify containers by their name or ID.
    """
    container_service = ContainerService(ctx.obj["config"])
    if all:
        container_list = [c["id"] for c in container_service.list_containers()]
    else:
        container_list = containers
    for c_id in container_list:
        container_service.stop_container(c_id)
        if remove:
            container_service.remove_container(c_id)


@cli.command(name="remove")
@click.argument("containers", nargs=-1, metavar="CONTAINER_NAME_OR_ID")
@click.option(
    "--all", is_flag=True, help="Remove all stopped ispawn containers."
)
@click.pass_context
def remove_container(ctx, containers, all):
    """
    Remove one or more stopped ispawn containers.

    Containers must be stopped before they can be removed, unless --force is
    used.
    You can specify containers by their name or ID.
    """
    container_service = ContainerService(ctx.obj["config"])
    if all:
        container_list = [c["id"] for c in container_service.list_containers()]
    else:
        container_list = containers
    for c_id in container_list:
        container_service.remove_container(c_id, ctx.obj["force"])


@cli.command(name="status")
@click.pass_context
def status(ctx):
    """
    Show the current project status.

    Displays the current configuration settings, running containers,
    and checks if the Traefik proxy container is running.
    """
    config = ctx.obj["config"]
    container_service = ContainerService(config)
    
    # Display configuration information
    click.echo(click.style("Configuration:", fg="blue", bold=True))
    config_table = [
        ["Name", config.name],
        ["Network Name", config.network_name],
        ["Domain", config.domain],
        ["Domain Prefix", config.domain_prefix],
        ["Proxy Mode", config.mode.value],
        ["Install Mode", config.install_mode.value],
        ["Subnet", config.subnet],
        ["Mount Point", config.mount_point],
        ["User in Namespace", "Yes" if config.user_in_namespace else "No"],
        ["Timezone", config.timezone],
        ["Home Prefix", config.home_prefix],
        ["DNS Servers", ", ".join(config.dns)],
        ["Config Directory", config.config_dir],
        ["User Root Directory", config.user_root_dir],
        ["Log Directory", config.base_log_dir],
        ["Image Name Prefix", config.image_name_prefix],
        ["Container Name Prefix", config.container_name_prefix],
    ]
    
    # Add certificate-related configuration if in remote mode
    if config.mode == ProxyMode.REMOTE and config.cert_mode:
        config_table.append(["Certificate Mode", config.cert_mode.value])
        if config.cert_mode == CertMode.PROVIDED and config.cert_dir:
            config_table.append(["Certificate Directory", config.cert_dir])
        elif config.cert_mode == CertMode.LETSENCRYPT and config.email:
            config_table.append(["Email for Let's Encrypt", config.email])
    
    # Add build customization paths if set
    if config.env_chunk_path:
        config_table.append(["Environment Chunk Path", config.env_chunk_path])
    if config.dockerfile_chunk_path:
        config_table.append(["Dockerfile Chunk Path", config.dockerfile_chunk_path])
    if config.entrypoint_chunk_path:
        config_table.append(["Entrypoint Chunk Path", config.entrypoint_chunk_path])
    
    click.echo(tabulate(config_table, tablefmt="simple"))
    
    # Display default volumes if any
    if config.volumes:
        click.echo("\n" + click.style("Default Volumes:", fg="blue", bold=True))
        volumes_table = []
        for vol in config.volumes:
            mode = "ro" if len(vol) > 2 and vol[2] == "ro" else "rw"
            volumes_table.append([vol[0], vol[1], mode])
        click.echo(tabulate(volumes_table, headers=["Host Path", "Container Path", "Mode"], tablefmt="simple"))
    
    # Check if Traefik container is running
    click.echo("\n" + click.style("Traefik Status:", fg="blue", bold=True))
    
    # Use Docker client directly to check for Traefik container
    # The ContainerService's list_containers method excludes containers ending with "-traefik"
    traefik_container_name = f"{config.name}-traefik"
    traefik_found = False
    
    try:
        # Get all containers and filter for Traefik
        all_containers = container_service.client.containers.list(all=True)
        for container in all_containers:
            if container.name == traefik_container_name:
                traefik_found = True
                traefik_id = container.short_id
                traefik_status = container.status
                traefik_running = container.status.lower() == "running"
                
                if traefik_running:
                    click.echo(click.style(f"✓ Traefik proxy is running", fg="green"))
                    click.echo(f"  Name: {container.name}")
                    click.echo(f"  ID: {traefik_id}")
                    click.echo(f"  Status: {traefik_status}")
                    
                    # Get container image
                    try:
                        image_name = container.image.tags[0] if container.image.tags else container.image.short_id
                        click.echo(f"  Image: {image_name}")
                    except Exception:
                        pass
                else:
                    click.echo(click.style(f"! Traefik proxy exists but is not running", fg="yellow"))
                    click.echo(f"  Name: {container.name}")
                    click.echo(f"  ID: {traefik_id}")
                    click.echo(f"  Status: {traefik_status}")
                break
        
        if not traefik_found:
            click.echo(click.style("✗ Traefik proxy container not found", fg="red"))
            click.echo("  Run 'ispawn setup' to create the Traefik container")
    except Exception as e:
        click.echo(click.style(f"! Error checking Traefik status: {str(e)}", fg="red"))
