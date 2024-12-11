import os
import sys
import subprocess
import getpass
from ispawn.utils import *
from command_runner import command_runner
from pathlib import Path
import yaml
import random
import string

def generate_labels(service, name, domain, container_name):
  if service == 'rstudio':
    port = 8787
  elif service == 'jupyter':
    port = 8888
  elif service == 'vscode':
    port = 8842
  else:
    raise ValueError(f'Unknown service: {service}')
  return [
    "--label", f"traefik.http.services.{container_name}-{service}.loadbalancer.server.port={port}",
    "--label", f"traefik.http.routers.{container_name}-{service}-https.rule=Host(`{service}-{name}.{domain}`)",
    "--label", f"traefik.http.routers.{container_name}-{service}-https.service={container_name}-{service}",
    "--label", f"traefik.http.routers.{container_name}-{service}-https.tls=true",
    "--label", f"traefik.http.routers.{container_name}-{service}-http.rule=Host(`{service}-{name}.{domain}`)",
    "--label", f"traefik.http.routers.{container_name}-{service}-http.entrypoints=web",
    "--label", f"traefik.http.routers.{container_name}-{service}-http.middlewares=redirect-to-https@docker"
  ]

def run_container(args):
  # Setup
  username = args.username if args.username else getpass.getuser()
  ## get password or generate 8 chars password
  password = args.password if args.password else ''.join(random.choices(string.ascii_letters + string.digits, k=8))
  uid = args.uid if args.uid else os.getuid()
  gid = args.gid if args.gid else os.getgid()
  container_name = f"{args.name_prefix}-{args.name}"

  # Map ports based on the selected services
  services = args.services.split(',')
  services = [service.strip() for service in services]

  images = get_docker_images(args)
  target = get_image_target(args, services)

  if target not in [ im["Repository"] + ":" + im["Tag"] for im in images]:
    print(f"Image '{target}' not found. Please build the image first using 'ispawn image build'.")
    return

  # Check if container is already running
  running_containers = get_running_containers(args)
  if container_name in [ct["Name"] for ct in running_containers]:
      print(f"Container '{container_name}' is already running.")
      if args.force:
          print(f"Stopping and removing the container '{container_name}'.")
          subprocess.run(['docker', 'stop', container_name], check=True)
          subprocess.run(['docker', 'rm', container_name], check=True)
      else:
          print(f"Use --force to stop and remove the existing container.")
          return

  config = yaml.safe_load(open("/etc/ispawn/config.yml"))

  # Prepare docker run command
  docker_command = [
      'docker', 'run', '-d',
      '--name', container_name,
      '--network', config["name"]
  ]

  docker_command.extend([  
    '--label',
    'traefik.enable=true',  
    '--label',
    'traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https'  
  ])

  domain = config["web"]["domain"]

  for service in services:
    docker_command.extend(
      generate_labels(service, args.name, domain, container_name)
    )

  # Handle volume mounts
  if not args.volumes:
    args.volumes = str(Path.home())

  print(args.volumes)

  if args.volumes:
      if args.volumes == "":
        args.volumes = Path.home()
      volumes = args.volumes.split(",")
      for volume in volumes:
          docker_command.extend([
              "-v", f"{volume}:{args.mount_prefix}/{volume}"
          ])

  # Pass environment variables for user setup
  docker_command.extend([
      '-e', f'USERNAME={username}',
      '-e', f'PASSWORD={password}',
      '-e', f'UID={uid}',
      '-e', f'GID={gid}',
  ])

  for dns in args.dns.split(","):
     docker_command.extend(['--dns', dns])

  docker_command.append(target)
  docker_command.append("sleep infinity")

  # Run the Docker container
  print("Running Docker container...")
  exit_code, output = command_runner(" ".join(docker_command), live_output=True)
  if exit_code != 0:
    print("An error occurred while running the Docker image.")
    sys.exit(1)

  print(f"Docker container '{container_name}' is running.")
  print(f"Access services at:")
  for service in services:
    if service == "rstudio":
      print(f" - {service}: https://{service}-{args.name}.{domain}")
      print(f"   - Username: {username}")
      print(f"   - Password: {password}")
      print("---")
    elif service == "vscode":
      print(f" - {service}: http://{service}-{args.name}.{domain}?tkn={password}")
    elif service == "jupyter":
      print(f" - {service}: http://{service}-{args.name}.{domain}")
      print(f"   - Token: {password}")
  
