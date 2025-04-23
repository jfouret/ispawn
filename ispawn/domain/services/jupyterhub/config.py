"""JupyterHub service configuration."""

PORT = 8000

# Map container paths to host directory names
VOLUMES = {
    "jupyterhub_data": "~/.local/share/jupyterhub",
    "jupyterhub_config": "~/.jupyterhub",
    "jupyter": "~/.jupyter",
    "ipython": "~/.ipython",
    "local_jupyter": "~/.local/share/jupyter",
}
