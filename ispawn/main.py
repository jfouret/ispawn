import argparse
from ispawn.commands import image, run, list_containers, setup

def main():
  parser = argparse.ArgumentParser(prog='ispawn', description=
    'A tool to build and run Docker images for RStudio Server and Jupyter.')
  parser.add_argument('--name-prefix', default='ispawn', 
    help='Prefix for the image and container name')

  subparsers = parser.add_subparsers(dest='command', help='Available commands')


  # Subcommand: sys
  setup_parser = subparsers.add_parser("setup", help = "Configure system")
  setup_parser.add_argument("--domain", default = "ispawn.localhost",
    help = "Domain name for the server")
  setup_parser.add_argument("--mode", choices = ["local", "remote"],
    default = "local",
    help = "If the server is accessed from localhost (local) or remotely")
  setup_parser.add_argument("--cert", required = False,
    help="Path to the SSL certificate")
  setup_parser.add_argument("--key", required = False,
    help="Path to the SSL private key")
  setup_parser.add_argument("--subnet", default = "172.30.192.0/24",
    help="Subnet for the Docker network (default: 172.30.192.0/24)")
  setup_parser.add_argument("--env_file", default = None,
    help="".join([
      "Path for default environment file, to be appended in /etc/environment",
      "stored in /etc/ispawn/environment"
    ]))
  setup_parser.add_argument("--setup_file", default = None,
    help="".join([
      "Path for default setup file, to be executed when image is built",
      "stored in /etc/ispawn/setup"
    ]))


  # Subcommand: image
  image_parser = subparsers.add_parser('image', help='Manage images')
  image_subparsers = image_parser.add_subparsers(dest='subcommand',
    help='Image commands')

  # image build
  image_build_parser = image_subparsers.add_parser('build', 
    help='Build a new Docker image')
  image_build_parser.add_argument('--image', required=True,
    help='Base image for the Docker container')
  image_build_parser.add_argument('--services',
    default='rstudio,jupyter,vscode',
    help="".join([
      "Services to include: rstudio, jupyter, and/or vscode ",
      "(default: rstudio,jupyter,vscode)"
    ]))
  image_build_parser.add_argument("--env_file", default = None, help=
    "Path for default environment file, to be appended in /etc/environment")
  image_build_parser.add_argument("--setup_file", default = None,
    help="Path for default setup file, to be executed when image is built")



  # image list
  image_subparsers.add_parser('list', help='List built images')

  # image rm
  image_rm_parser = image_subparsers.add_parser('rm', help='Remove images')
  image_rm_parser.add_argument('--all', action='store_true', help='Remove all images built by ispawn')
  image_rm_parser.add_argument('image_names', nargs='*', help='Names of images to remove')

  # Subcommand: run
  run_parser = subparsers.add_parser('run', help='Run a container based on a built image')
  run_parser.add_argument('--name', default='local', 
    help='Name for the container (default: local)')
  run_parser.add_argument('--image', required=True, 
    help='Base image for the Docker container')
  run_parser.add_argument('--services',
    default='rstudio,jupyter,vscode',
    help="".join([
      "Services to include: rstudio, jupyter, and/or vscode ",
      "(default: rstudio,jupyter,vscode)"
    ]))
  run_parser.add_argument('--username', default=None, help='Username for the Docker container (default: current user)')
  run_parser.add_argument('--password', default=None, help='Password for the user in the Docker container')
  run_parser.add_argument('--uid', type=int, default=None, help='User ID for the Docker container (default: UID of current user)')
  run_parser.add_argument('--gid', type=int, default=None, help='Group ID for the Docker container (default: GID of current user)')
  run_parser.add_argument('--dns', default="8.8.8.8,8.8.4.4", help='Comma-separated list of dns servers to use (default: 8.8.8.8,8.8.4.4)')
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
  elif args.command == 'setup':
      setup.ISpawnSetup(args)
  else:
      parser.print_help()

if __name__ == '__main__':
  main()