import argparse
from ispawn.commands import image, run, list_containers

def main():
  parser = argparse.ArgumentParser(prog='ispawn', description='A tool to build and run Docker images for RStudio Server and Jupyter.')
  parser.add_argument('--name-prefix', default='ispawn', help='Prefix for the image and container name')

  subparsers = parser.add_subparsers(dest='command', help='Available commands')

  # Subcommand: image
  image_parser = subparsers.add_parser('image', help='Manage images')
  image_subparsers = image_parser.add_subparsers(dest='subcommand', help='Image commands')

  # image build
  image_build_parser = image_subparsers.add_parser('build', help='Build a new Docker image')
  image_build_parser.add_argument('--image', required=True, help='Base image for the Docker container')
  image_build_parser.add_argument('--services', default='rstudio', help='Services to include: rstudio, jupyter, or both (default: rstudio)')

  # image list
  image_subparsers.add_parser('list', help='List built images')

  # image rm
  image_rm_parser = image_subparsers.add_parser('rm', help='Remove images')
  image_rm_parser.add_argument('--all', action='store_true', help='Remove all images built by ispawn')
  image_rm_parser.add_argument('image_names', nargs='*', help='Names of images to remove')

  # Subcommand: run
  run_parser = subparsers.add_parser('run', help='Run a container based on a built image')
  run_parser.add_argument('--name', default='local', help='Name for the container (default: local)')
  run_parser.add_argument('--image', required=True, help='Base image for the Docker container')
  run_parser.add_argument('--services', default='rstudio', help='Services to run: rstudio, jupyter, or both (default: rstudio)')
  run_parser.add_argument('--rstudio-port', type=int, default=8787, help='Port for RStudio Server (default: 8787)')
  run_parser.add_argument('--jupyter-port', type=int, default=8888, help='Port for Jupyter Notebook (default: 8888)')
  run_parser.add_argument('--username', default=None, help='Username for the Docker container (default: current user)')
  run_parser.add_argument('--password', required=True, help='Password for the user in the Docker container')
  run_parser.add_argument('--uid', type=int, default=None, help='User ID for the Docker container (default: UID of current user)')
  run_parser.add_argument('--gid', type=int, default=None, help='Group ID for the Docker container (default: GID of current user)')
  run_parser.add_argument('--volumes', default=None, help='Comma-separated list of volumes to mount (default: user home)')
  run_parser.add_argument('--mount-prefix', default='/host', help='Prefix for volume mounts inside the container (default: /host)')
  run_parser.add_argument('--force', action='store_true', help='Force stopping and removal of an existing container if it exists')

  # Subcommand: list
  subparsers.add_parser('list', help='List running containers started by ispawn')

  args = parser.parse_args()

  if args.command == 'image':
      if args.subcommand == 'build':
          image.build(args)
      elif args.subcommand == 'list':
          image.list_images(args)
      elif args.subcommand == 'rm':
          image.remove_images(args)
      else:
          image_parser.print_help()
  elif args.command == 'run':
      run.run_container(args)
  elif args.command == 'list':
      list_containers.list_running_containers(args)
  else:
      parser.print_help()

if __name__ == '__main__':
  main()