import os
import sys
import subprocess
import getpass
from ispawn.utils import *
from command_runner import command_runner
from pathlib import Path

def run_container(args):
  # Setup
  username = args.username if args.username else getpass.getuser()
  uid = args.uid if args.uid else os.getuid()
  gid = args.gid if args.gid else os.getgid()
  container_name = f"{args.name_prefix}-{args.name}"

  # Map ports based on the selected services
  services = args.services.split(',')
  services = [service.strip() for service in services]

  if len(services) != 1:
    print("One and Only One service required for running", file=sys.stderr)
    sys.exit(1)

  service = services[0]
  images = get_docker_images(args)
  target = get_image_target(args, service)

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

  # Prepare docker run command
  docker_command = [
      'docker', 'run', '-d',
      '--name', container_name,
  ]

  if 'rstudio' in services:
      docker_command.extend(['-p', f"{args.rstudio_port}:8787"])
  if 'jupyter' in services:
      docker_command.extend(['-p', f"{args.jupyter_port}:8888"])

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
      '-e', f'PASSWORD={args.password}',
      '-e', f'UID={uid}',
      '-e', f'GID={gid}',
  ])

  docker_command.append(target)
  docker_command.append("sleep infinity")


  # Run the Docker container
  exit_code, output = command_runner(" ".join(docker_command), live_output=True)
  if exit_code != 0:
    print("An error occurred while running the Docker image.")
    sys.exit(1)

  print(f"Docker container '{container_name}' is running.")
  print(f"Access services at:")
  if 'rstudio' in services:
      print(f" - RStudio Server: http://127.0.0.1:{args.rstudio_port}")
  if 'jupyter' in services:
      print(f" - Jupyter Notebook: http://127.0.0.1:{args.jupyter_port}")