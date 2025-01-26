#!/bin/bash

# Run jupyter notebook with the specified options
sudo -u "$USER_NAME" bash -c \
    'cd ~ && \
    eval "$(micromamba shell hook --shell bash --root-prefix /opt/conda)" && \
    export MAMBA_ROOT_PREFIX=/opt/conda && \
    micromamba activate jupyter_ispawn && \
    jupyter notebook \
        --ip=0.0.0.0 \
        --port=8888 \
        --ServerApp.token='"$USER_PASS"' \
        --notebook-dir="/" \
        --preferred-dir="$HOME" \
        --no-browser' \
    > "${LOG_DIR}/services/jupyter.log" 2>&1 &
