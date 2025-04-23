"""JupyterLab service configuration."""

PORT = 8889

# Map container paths to host directory names
VOLUMES = {
    "jupyter": "~/.jupyter",
    "ipython": "~/.ipython",
    "local_jupyter": "~/.local/share/jupyter",
}
