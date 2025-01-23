#!/bin/bash

# Activate the micromamba environment
eval "\$(micromamba shell hook --shell bash)"
micromamba activate ispawn_jupyter

# Run jupyter notebook with the specified options
sudo -u "$USER_NAME" jupyter notebook \
    --ip=0.0.0.0 \
    --port=8888 \
    --NotebookApp.token="$USER_PASS" \
    --no-browser \
    > "${LOG_DIR}/services/jupyter.log" 2>&1 &

