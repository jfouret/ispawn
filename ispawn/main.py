import click
from pathlib import Path
from typing import List
import sys
from datetime import datetime
from tabulate import tabulate

from ispawn.domain.config import InstallMode, CertMode, ProxyMode, Config
from ispawn.services.config import ConfigManager
from ispawn.domain.image import Service, ImageConfig
from ispawn.services.image import ImageService
from ispawn.services.container import ContainerService
from ispawn.domain.container import ContainerConfig

import re

def is_valid_path(path):
    return bool(re.match(r'^/[a-zA-Z0-9\-_\. /]+$', path)) and '//' not in path

def parse_volumes(volumes, mnt):
    results = []
    for volume in volumes:
        if ':' in volume:
            parsed = volume.split(':')
            if len(parsed) > 3:
                raise ValueError(f"Volume {volume} is not valid")
            if len(parsed) == 3:
                if parsed[2] not in ['ro', 'rw']:
                    raise ValueError(f"Volume {volume} is not valid")
            results.append(parsed)
        else:
            p1 = mnt.rstrip('/')
            p2 = volume.lstrip('/').rstrip('/')
            results.append([f"{volume}", f"{p1}/{p2}"])
    for volume in results:
        # test the the first exists and make it absolute
        volume[0] = str(Path(volume[0]).resolve(strict=True))
        # test that the second is a possible path (no forbidden chars)
        if not is_valid_path(volume[1]):
            raise ValueError(f"Volume {volume[1]} is not valid")
    return results

@click.group()
@click.option('-f', '--force',
              default = False,
              is_flag = True,
              help = 'Overwrite existing')
@click.option('-u', '--user',
              default = False,
              is_flag = True,
              help = 'Priorize user config over system config')
@click.pass_context
def cli(ctx, force, user):
    ctx.obj = {
      'force': force,
      'user': user
    }
    config = Config.load(user_mode = user)
    if config is None:
        config = Config.load(user_mode = (not user))
    if config is not None:
        ctx.obj['config'] = config
    if "config" not in ctx.obj.keys() and ctx.invoked_subcommand != 'setup':
        click.echo(click.style("Error: No valid config found, run ispawn setup", fg='red'), err=True)
        print(ctx.obj)
        sys.exit(1)

@cli.command()
@click.option('-n', '--name',
              default="ispawn",
              help="Name for docker namespace"
              )
@click.option('-m', '--mode', 
              default = ProxyMode.LOCAL.value,
              type=click.Choice([m.value for m in ProxyMode]),
              help='Proxy mode, from where do the client connect (local or remote)')
@click.option('-d', '--domain',
              default = 'ispawn.localhost',
              help='Domain name')
@click.option('--install-mode',
              default=InstallMode.USER.value,
              type=click.Choice([m.value for m in InstallMode]),
              help='Where to install (user in ~/.ispawn or system in /etc/ispawn)')
@click.option('--subnet',
              default='172.30.0.0/24', 
              help='Subnet CIDR string (docker internal subnet)')
@click.option('--user-in-namespace',
              is_flag = True,
              help= 'If set, add username to namespace when running container')
@click.option('--cert-mode',
              type=click.Choice([m.value for m in CertMode]),
              help='If Remote, Certificate mode (letsencrypt or provided)')
@click.option('--cert-dir',
              help = 'If provided, directory containing SSL certificate (cert.pem) and key (key.pem)'
              )
@click.option('--email',
              help='if Letsencrypt, email')
@click.option('-v', '--volume', 'volumes',
              help='Volumes to mount in containers by default, can specify a mount point with :',
              multiple = True)
@click.option('--mount-point',
              help='Default mount point for volumes (if : not specified in volume)',
              default = '/mnt')
@click.option('--dns',
              default = ["8.8.8.8", "8.8.4.4"],
              multiple=True,
              help='')
@click.option('--env-chunk-path', type=click.Path(exists=True, path_type=str),
              help='Default path to environment file for Docker builds')
@click.option('--dockerfile-chunk-path', type=click.Path(exists=True, path_type=str),
              help='Default path to dockerfile chunk for Docker builds')
@click.option('--entrypoint-chunk-path', type=click.Path(exists=True, path_type=str),
              help='Default path to entrypoint chunk for Docker builds')
@click.pass_context
def setup(ctx, **kwargs):
    """Setup ispawn environment."""
    kwargs['dns'] = [ ip for ip in kwargs['dns'] ]
    kwargs['volumes'] = parse_volumes(kwargs['volumes'], kwargs['mount_point'])
    config = Config(**kwargs)
    config_manager = ConfigManager(config, ctx.obj['force'])
    config_manager.apply_config()

@cli.command(name='build')
@click.option('-b', '--base', required=True, help='Base image')
@click.option('-s', '--service', 'services', multiple=True,
              type=click.Choice([s.value for s in Service], case_sensitive=False),
              help='Services to run (can be specified multiple times). Defaults to vscode, rstudio, and jupyter if not specified.')
@click.pass_context
def build(ctx, **kwargs):
    """Build a Docker image."""
    # Set default services if none specified
    if "services" not in kwargs.keys():
        kwargs["services"] = []
    if len(kwargs["services"]) == 0:
        kwargs["services"] = ["vscode", "rstudio", "jupyter"]
    kwargs["config"] = ctx.obj['config']
    image_config = ImageConfig(**kwargs)
    im = ImageService(ctx.obj['config'])
    im.build_image(image_config)

@cli.group()
def image():
    """Manage Docker images."""
    pass

@image.command(name='list')
@click.pass_context
def list_cmd(ctx):
    """List Docker images."""
    im = ImageService(ctx.obj['config'])
    images = im.list_images()
    table = tabulate(
        [
            [ image['id'],
              " ".join(image['tags']),
              image['size'],
              image['created'].split('.')[0].replace('T', ' ')
            ]
            for image in images
        ],
        headers=['ID', 'TAGS', 'SIZE', 'CREATED (YYYY-MM-DD)']
    )
    click.echo(table)

@image.command(name='remove')
@click.argument('images', nargs=-1)
@click.option('--all', is_flag=True, help='Remove all images')
@click.pass_context
def remove(ctx, images: List[str], all: bool):
    """Remove Docker images."""
    im = ImageService(ctx.obj['config'])
    for digest in images:
        im.remove_image(digest, force = ctx.obj["force"])
    if all:
        for image in im.list_images():
            im.remove_image(image['id'], force = ctx.obj["force"])

@cli.command()
@click.option('-n', '--name', required=True, help='Container name')
@click.option('-b' ,'--base', required=True, help='Base docker image')
@click.option('--build', is_flag=True,  help='Build image if missing')
@click.option('-s', '--service', 'services', multiple=True,
              type=click.Choice([s.value for s in Service], case_sensitive=False),
              help='Services to run (can be specified multiple times). Defaults to vscode, rstudio, and jupyter if not specified.')
@click.option('-v', '--volume', 'volumes', multiple=True,
              help='Volume mounts (can be specified multiple times)')
@click.option('-g', '--group',
              help='Required group for RStudio access (defaults to username)')
@click.pass_context
def run(ctx, name, base: str, services: List[str], volumes: List[str], build, group: str):
    """Run a container."""
    try:
        # Parse volumes
        parsed_volumes = parse_volumes(volumes, ctx.obj['config'].mount_point)
        
        # Set default services if none specified
        if not services:
            services = []
        if len(services) == 0:
            services = ["vscode", "rstudio", "jupyter"]
        
        # Create image config
        image_config = ImageConfig(
            base=base,
            services=[Service(s) for s in services],
            config=ctx.obj['config']
        )

        im = ImageService(ctx.obj['config'])
        if not im.check_image(image_config):
            if build:
                im.build_image(image_config)
            else:
                print(f"Image {image_config.target_image} not found. Use build command or --build to build it.")
                sys.exit(1)
        
        # Create container config
        container_config = ContainerConfig(
            name=name,
            config=ctx.obj['config'],
            image_config=image_config,
            volumes=parsed_volumes,
            group=group
        )
        
        # Initialize container service
        container_service = ContainerService(ctx.obj['config'])
        
        # Run container
        container = container_service.run_container(container_config, force=ctx.obj['force'])
        click.echo(f"Container {container.name} started successfully")
        
        # Display service URLs
        click.echo("\nService URLs:")
        for service in container_config.image_config.services:
            domain = container_config.get_service_domain(service)
            click.echo(f"{service.value}: https://{domain}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command(name='list')
@click.pass_context
def list_containers(ctx):
    """List running containers."""
    try:
        container_service = ContainerService(ctx.obj['config'])
        containers = container_service.list_containers()
        if not containers:
            click.echo("No containers found")
            return
        table = tabulate(
            [
                [
                    container['name'],
                    container['id'],
                    container['status'],
                    container['image']
                ]
                for container in containers
            ],
            headers=['NAME', 'ID', 'STATUS', 'IMAGE']
        )
        click.echo(table)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command(name='stop')
@click.argument('containers', nargs = -1)
@click.option('--all', is_flag=True, help='Stop all running containers')
@click.option('--remove', is_flag=True, help='Remove also the containers')
@click.pass_context
def stop(ctx, containers, all, remove):
    """Stop a running container."""
    container_service = ContainerService(ctx.obj['config'])
    if all:
        container_list = [c["id"] for c in container_service.list_containers()]
    else:
        container_list = containers
    for c_id in container_list:
        container_service.stop_container(c_id)
        if remove:
            container_service.remove_container(c_id)

@cli.command(name="remove")
@click.argument('containers', nargs = -1)
@click.option('--all', is_flag=True, help='Remove all containers')
@click.pass_context
def remove(ctx, containers, all):
    """Remove a container."""
    container_service = ContainerService(ctx.obj['config'])
    if all:
        container_list = [c["id"] for c in container_service.list_containers()]
    else:
        container_list = containers
    for c_id in container_list:
        container_service.remove_container(c_id, ctx.obj['force'])
