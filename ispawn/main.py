import click
from pathlib import Path
from typing import List
import sys

from ispawn.config import Config, Mode, CertMode
from ispawn.commands.setup import setup_command
from ispawn.commands.run import run_container
from ispawn.commands.image import build_image, list_images, remove_images
from ispawn.commands.list_containers import list_running_containers
from ispawn.commands.logs import logs_command

@click.group()
@click.option('--config', type=click.Path(exists=True, path_type=Path),
              help='Path to configuration file')
@click.pass_context
def cli(ctx, config: Path):
    """ispawn - Interactive Scientific Python Workspace And Notebook."""
    try:
        ctx.ensure_object(dict)
        ctx.obj['config'] = Config(config)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--mode', type=click.Choice([m.value for m in Mode]),
              help='Deployment mode (local or remote)')
@click.option('--domain', help='Domain name')
@click.option('--subnet', help='Subnet configuration')
@click.option('--cert-mode', type=click.Choice([m.value for m in CertMode]),
              help='Certificate mode for remote deployment (letsencrypt or provided)')
@click.option('--email', help='Email for Let\'s Encrypt certificates')
@click.option('--env-file', type=click.Path(exists=True, path_type=Path),
              help='Path to environment file')
@click.pass_context
def setup(ctx, mode, domain, subnet, cert_mode, email, env_file):
    """Setup ispawn environment."""
    try:
        setup_command(
            config=ctx.obj['config'],
            mode=mode,
            domain=domain,
            subnet=subnet,
            cert_mode=cert_mode,
            email=email,
            env_file=env_file
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

@cli.group()
def image():
    """Manage Docker images."""
    pass

@image.command(name='build')
@click.option('--base', required=True, help='Base image')
@click.option('--name', required=True, help='Image name')
@click.option('--service', 'services', multiple=True, required=True,
              type=click.Choice(['jupyter', 'rstudio', 'vscode']),
              help='Services to include (can be specified multiple times)')
@click.option('--env-file', type=click.Path(exists=True, path_type=Path),
              help='Path to environment file')
@click.option('--setup-file', type=click.Path(exists=True, path_type=Path),
              help='Path to setup script')
@click.pass_context
def build(ctx, base, name, services, env_file, setup_file):
    """Build a Docker image."""
    try:
        build_image(
            config=ctx.obj['config'],
            base_image=base,
            name=name,
            services=services,
            env_file=env_file,
            setup_file=setup_file
        )
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

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

if __name__ == '__main__':
    cli()
