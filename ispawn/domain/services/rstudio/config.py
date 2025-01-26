"""RStudio service configuration."""

PORT = 8787

# Map container paths to host directory names
VOLUMES = {
    "share" : "~/.local/share/rstudio"
}
