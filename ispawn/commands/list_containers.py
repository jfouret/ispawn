from ispawn.services.docker import DockerService

def list_running_containers(args):
    """List all running ispawn containers."""
    docker = DockerService()
    containers = docker.list_containers()

    if containers:
        print("Running containers:")
        print("NAME\t\tIMAGE\t\tSTATUS\t\tID")
        print("-" * 60)
        for container in containers:
            print(f"{container['name']}\t{container['image']}\t{container['status']}\t{container['id']}")
    else:
        print("No running containers started by ispawn.")
