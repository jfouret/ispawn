import click
from pathlib import Path
from typing import List
import sys
from datetime import datetime

from ispawn.domain.proxy import InstallMode, CertMode, ProxyMode, ProxyConfig
from ispawn.services.config import ConfigManager
from ispawn.domain.image import Service, ImageConfig
from ispawn.services.image import ImageService

@click.group()
@click.option('--force',
              default = False,
              is_flag = True,
              help = 'Overwrite existing')
@click.option('--user',
              default = False,
              is_flag = True,
              help = 'Priorize user config over system config')
@click.pass_context
def cli(ctx, force, user):
    ctx.obj = {
      'force': force,
      'user': user
    }
    config = ProxyConfig.load(user_mode = user)
    if config is None:
        config = ProxyConfig.load(user_mode = (not user))
    if config is not None:
        ctx.obj['config'] = config
    if "config" not in ctx.obj.keys() and ctx.invoked_subcommand != 'setup':
        click.echo(click.style("Error: No valid config found, run ispawn setup", fg='red'), err=True)
        print(ctx.obj)
        sys.exit(1)

@cli.command()
@click.option('--install-mode',
              default=InstallMode.USER.value,
              type=click.Choice([m.value for m in InstallMode]),
              help='Where to install (user in ~/.ispawn or system in /etc/ispawn)')
@click.option('--mode', 
              default = ProxyMode.LOCAL.value,
              type=click.Choice([m.value for m in ProxyMode]),
              help='Proxy mode, from where do the client connect (local or remote)')
@click.option('--domain',
              default = 'ispawn.localhost',
              help='Domain name')
@click.option('--subnet',
              default='172.30.0.0/24', 
              help='Subnet CIDR string (docker internal subnet)')
@click.option('--name',
              default="ispawn",
              help="Name for docker namespace"
              )
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
@click.option('--volumes',
              help='Comma separated list of volumes to mounts by default',
              default = '~')
@click.option('--mount-point',
              help='Default mount point for volumes',
              default = '/mnt')
@click.pass_context
def setup(ctx, **kwargs):
    """Setup ispawn environment."""
    kwargs['volumes'] = kwargs['volumes'].split(',')
    proxy_config = ProxyConfig(**kwargs)
    config_manager = ConfigManager(proxy_config, ctx.obj['force'])
    config_manager.apply_config()

@cli.group()
def image():
    """Manage Docker images."""
    pass

@image.command(name='build')
@click.option('-b', '--base', required=True, help='Base image')
@click.option('-s', '--service', 'services', multiple=True, required=True,
              type=click.Choice([s.value for s in Service], case_sensitive=False),
              help='Services to include (can be specified multiple times)')
@click.option('-e', '--env-chunk-path', type=click.Path(exists=True, path_type=str),
              help='Path to environment file')
@click.option('-d', '--dockerfile-chunk-path', type=click.Path(exists=True, path_type=str),
              help='Path to dockerfile chunk to add to the image')
@click.option('-i','--entrypoint-chunk-path', type=click.Path(exists=True, path_type=str),
              help='Path to entrypoint chunk to add to the image')
@click.pass_context
def build(ctx, **kwargs):
    """Build a Docker image."""
    kwargs["proxy_config"] = ctx.obj['config']
    image_config = ImageConfig(**kwargs)
    im = ImageService(ctx.obj['config'])
    im.build_image(image_config)

@image.command(name='list')
@click.pass_context
def list_cmd(ctx):
    """List Docker images."""
    im = ImageService()
    im.list_images()

@image.command(name='remove')
@click.argument('images', nargs=-1)
@click.option('--all', is_flag=True, help='Remove all images')
@click.pass_context
def remove(ctx, images: List[str], all: bool):
    """Remove Docker images."""
    try:
        remove_images(
            config=ctx.obj['config'],
            images=images,
            remove_all=all
        )
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--name', required=True, help='Container name')
@click.option('--image', required=True, help='Docker image')
@click.option('--service', 'services', multiple=True, required=True,
              type=click.Choice(['jupyter', 'rstudio', 'vscode']),
              help='Services to run (can be specified multiple times)')
@click.option('--username', help='Username for services')
@click.option('--password', help='Password for services')
@click.option('--uid', type=int, help='User ID')
@click.option('--gid', type=int, help='Group ID')
@click.option('--volume', 'volumes', multiple=True,
              help='Volume mounts (can be specified multiple times)')
@click.option('--force/--no-force', default=False,
              help='Force replace existing container')
@click.pass_context
def run(ctx, name, image, services, username, password, uid, gid, volumes, force):
    """Run a container."""
    try:
        run_container(
            config=ctx.obj['config'],
            name=name,
            image=image,
            services=services,
            username=username,
            password=password,
            uid=uid,
            gid=gid,
            volumes=volumes,
            force=force
        )
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command(name='list')
@click.pass_context
def list_cmd(ctx):
    """List running containers."""
    try:
        list_running_containers(config=ctx.obj['config'])
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('container')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.pass_context
def logs(ctx, container: str, follow: bool):
    """Display container logs."""
    try:
        logs_command(
            config=ctx.obj['config'],
            container_name=container,
            follow=follow
        )
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
