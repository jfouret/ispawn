import subprocess
from ispawn.utils import *

def list_running_containers(args):

  running_containers = get_running_containers(args)

  keys = ["Name", "Ports", "Volumes", "Status", "Image"]

  if len(running_containers) > 0:
    print("Running containers:")
    print("\t".join(keys))
    for ct in running_containers:
      print("\t".join([ct[key] for key in keys]))
  else:
    print("No running containers started by ispawn.")