"""Jupyter service configuration."""

PORT = 8888

# Map host directory names to container paths
VOLUMES = {
    "jupyter": "~/.jupyter",
    "ipython": "~/.ipython",
    "local_jupyter": "~/.local/share/jupyter",
}
