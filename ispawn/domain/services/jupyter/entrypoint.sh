#!/bin/bash

# Activate the micromamba environment
eval "\$(micromamba shell hook --shell bash)"
micromamba activate ispawn_jupyter

# Run jupyter notebook with the specified options
sudo -u "$USERNAME" jupyter notebook \
    --ip=0.0.0.0 \
    --port=8888 \
    --NotebookApp.token="$PASSWORD" \
    --no-browser \
    > "${LOG_DIR}/jupyter/jupyter.log" 2>&1 &

