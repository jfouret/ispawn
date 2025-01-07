import click
from pathlib import Path
from typing import List
import sys
from datetime import datetime

from ispawn.domain.proxy import InstallMode, CertMode, ProxyMode, ProxyConfig
from ispawn.services.config import ConfigManager

from ispawn.domain.image import Service, ImageConfig

#from ispawn.commands.setup import setup_command
#from ispawn.commands.run import run_container
#from ispawn.commands.image import build_image, list_images, remove_images
#from ispawn.commands.list_containers import list_running_containers
#from ispawn.commands.logs import logs_command

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
    ctx.obj = {'force': force}
    user_config = Path.home() / '.ispawn' / 'config.yaml'
    system_config = Path('/etc/ispawn/config.yaml')
    if user:
        configs = [user_config, system_config]
    else:
        configs = [system_config, user_config]
    
    if all(c.exists() for c in configs):
        warning_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - WARN: 2 configs found both at user-lever ({user_config}) and system-level ({system_config})."
        click.echo(click.style(warning_msg, fg='yellow'), err=True)
        if not user:
            warning_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - WARN: system config in {system_config} will be used as default, use --user to change this behaviour"
            click.echo(click.style(warning_msg, fg='yellow'), err=True)
    
    for config in configs:
        if config.exists():
            ctx.obj['config'] = ProxyConfig.from_yaml(open(config,"r"))
            info_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO: Loaded config from {config}"
            click.echo(click.style(info_msg, fg='green'))
            break
    
    if "config" not in ctx.obj and ctx.invoked_subcommand != 'setup':
        click.echo(click.style("Error: No valid config found, run ispawn setup", fg='red'), err=True)
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

@click.pass_context
def setup(ctx, **kwargs):
    """Setup ispawn environment."""
    proxy_config = ProxyConfig(**kwargs)
    config_manager = ConfigManager(proxy_config, ctx.obj['force'])
    config_manager.apply_config()

@cli.group()
def image():
    """Manage Docker images."""
    pass

@image.command(name='build')
@click.option('--base', required=True, help='Base image')
@click.option('--name', required=True, help='Image name')
@click.option('--service', 'services', multiple=True, required=True,
              type=click.Choice([s.value for s in Service]),
              help='Services to include (can be specified multiple times)')
@click.option('--env-file', type=click.Path(exists=True, path_type=Path),
              help='Path to environment file')
@click.option('--setup-file', type=click.Path(exists=True, path_type=Path),
              help='Path to setup script')
@click.pass_context
def build(ctx, **kwargs):
    """Build a Docker image."""
    kwargs["name"]
    image_config = ImageConfig(**kwargs)
    image_manager = ImageManager(image_config, ctx.obj['force'])
    image_manager.build_image()


@image.command(name='list')
@click.pass_context
def list_cmd(ctx):
    """List Docker images."""
    try:
        list_images(config=ctx.obj['config'])
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

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
