"""VSCode service configuration."""

PORT = 8080

# Map host directory names to container paths
VOLUMES = {
    "vscode": "~/.vscode",
    "config": "~/.config/Code"
}
