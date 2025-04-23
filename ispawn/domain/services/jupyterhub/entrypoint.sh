#!/bin/bash

# Create JupyterHub configuration directory
mkdir -p /etc/jupyterhub

# Create JupyterHub configuration file
cat > /etc/jupyterhub/jupyterhub_config.py << EOL
c = get_config()

# Basic configuration
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000

# Configure single-user server
c.Spawner.port = 8888
c.Spawner.ip = '0.0.0.0'
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = '127.0.0.1'

# Use PAM authenticator for system users
c.JupyterHub.authenticator_class = 'jupyterhub.auth.PAMAuthenticator'

# Group-based authentication
c.PAMAuthenticator.admin_groups = {'${REQUIRED_GROUP}'}
c.PAMAuthenticator.allowed_groups = {'${REQUIRED_GROUP}'}

# Spawn single-user servers with system user permissions
c.Spawner.default_url = '/lab'  # Use JupyterLab as default interface
# Configure environment for spawned servers
c.Spawner.environment = {
    'MAMBA_ROOT_PREFIX': '/opt/conda',
    'PATH': '/opt/conda/envs/jupyterhub_ispawn/bin:${PATH}'
}

# Configure spawner
c.LocalProcessSpawner.shell_cmd = ['bash', '-l', '-c']
c.Spawner.cmd = ['bash', '-l', '-c', 'exec jupyter lab']
c.Spawner.notebook_dir = '~'
c.Spawner.debug = True
EOL

# Start JupyterHub
echo "[$(date)] Starting JupyterHub server..."
if which jupyterhub > /dev/null 2>&1; then
    jupyterhub -f /etc/jupyterhub/jupyterhub_config.py > "${LOG_DIR}/services/jupyterhub.log" 2>&1 &
else
    eval "$(micromamba shell hook --shell bash --root-prefix /opt/conda)" && \
    export MAMBA_ROOT_PREFIX=/opt/conda && \
    micromamba activate jupyterhub_ispawn && \
    jupyterhub -f /etc/jupyterhub/jupyterhub_config.py > "${LOG_DIR}/services/jupyterhub.log" 2>&1 &
fi
