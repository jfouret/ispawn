import subprocess

def get_docker_images(args):
  format_string = '{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}'
  result = subprocess.run(['docker', 'images', '--format', format_string], capture_output=True, text=True)
  images = []
  for line in result.stdout.strip().split('\n'):
    if line:  # Ensure the line is not empty
      parts = line.split()
      if len(parts) == 3:
        repo_tag, image_id, size = parts
        repo, tag = repo_tag.split(':')
        if repo.startswith(args.name_prefix+"-"):
          images.append({
            'Repository': repo,
            'Tag': tag,
            'ID': image_id,
            'Size': size
          })
  return images

def get_running_containers(args):
  format_string = '{{.Names}};{{.Ports}};{{.Mounts}};{{.Status}};{{.Image}}'
  result = subprocess.run(['docker', 'ps', '-a', '--format', format_string], capture_output=True, text=True)
  containers = []
  for line in result.stdout.strip().split('\n'):
    if line:  # Ensure the line is not empty
      parts = line.split(";")
      if len(parts) == 5:
        name, ports, mounts, status, image = parts
        if name.startswith(args.name_prefix):
          containers.append({
            'Name': name,
            'Ports': ports,
            'Volumes': mounts,
            'Status': status,
            'Image': image
          })
  return containers

def get_image_target(args, services):
  service_tag = "-".join(services)
  target = args.image.split(":")
  if len(target) > 1: 
    return(f"{args.name_prefix}-{target[0]}:{target[1]}-{service_tag}")
  else:
    return(f"{args.name_prefix}-{target[0]}:latest-{service_tag}")
