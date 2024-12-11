import os
from command_runner import command_runner  
import tempfile
from jinja2 import Template
from ispawn.utils import *
import yaml

# Load the Dockerfile and entrypoint templates from the templates directory
DOCKERFILE_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'templates', 'Dockerfile.j2')
ENTRYPOINT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'templates', 'entrypoint.sh.j2')

def build(args):

  # Parse services
  services = args.services.split(',')
  services = [service.strip() for service in services]

  target = get_image_target(args, services)

  # Prepare context for template rendering
  context = {
    'image': args.image,
    'services': services,
    'config': {}
  }
  env_abspath = None
  if args.env_file is None:
    env_abspath = "/etc/ispawn/environment"
  else:
    env_abspath = os.path.abspath(args.env_file)
  
  if os.path.exists(env_abspath):
    context["config"]["env_file"] = env_abspath

  setup_abspath = None
  if args.setup_file is None:
    setup_abspath = "/etc/ispawn/setup"
  else:
    setup_abspath = os.path.abspath(args.setup_file)
  if os.path.exists(setup_abspath):
    context["config"]["setup_file"] = setup_abspath

  # Load and render Dockerfile template
  with open(DOCKERFILE_TEMPLATE_PATH, 'r') as file:
    dockerfile_template = Template(file.read())
  rendered_dockerfile = dockerfile_template.render(**context)

  # Load and render entrypoint script template
  with open(ENTRYPOINT_TEMPLATE_PATH, 'r') as file:
    entrypoint_template = Template(file.read())
  rendered_entrypoint = entrypoint_template.render(services=services)

  with tempfile.TemporaryDirectory() as temp_dir:
    temp_dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
    temp_entrypoint_path = os.path.join(temp_dir, 'entrypoint.sh')

    with open(temp_dockerfile_path, 'w') as temp_dockerfile:
      temp_dockerfile.write(rendered_dockerfile)
    with open(temp_entrypoint_path, 'w') as temp_entrypoint:
      temp_entrypoint.write(rendered_entrypoint)

    exit_code, output = command_runner(f'docker build -t {target} {temp_dir}', live_output=True)
    if exit_code != 0:
      print("An error occurred while building the Docker image.")
      print("Dockerfile content:")
      print(rendered_dockerfile)

def list_images(args):
  images = get_docker_images(args)
  if images:
    print("\t".join(["NAME","TAG","ID","SIZE"]))
    for image in images:
      print("\t".join([image[key] for key in ["Repository", "Tag", "ID", "Size"]]))
  else:
    print("No Docker images built by ispawn.")

def remove_images(args):
  if args.all:
    images = get_docker_images(args)
  else:
    images = args.image_names

  for image in images:
    subprocess.run(['docker', 'rmi', '-f', image["ID"]], check=True)
    print(f"Removed image '{image["Repository"]}:{image["Tag"]}'.")