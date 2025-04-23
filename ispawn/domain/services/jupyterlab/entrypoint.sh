#!/bin/bash

# Run jupyter lab with the specified options
sudo -u "$USER_NAME" bash -c \
    'cd ~ && \
    if which jupyter-lab > /dev/null 2>&1; then \
        jupyter lab \
            --ip=0.0.0.0 \
            --port=8889 \
            --ServerApp.token='"$USER_PASS"' \
            --notebook-dir="/" \
            --preferred-dir="$HOME" \
            --no-browser \
    else \
        eval "$(micromamba shell hook --shell bash --root-prefix /opt/conda)" && \
        export MAMBA_ROOT_PREFIX=/opt/conda && \
        micromamba activate jupyterlab_ispawn && \
        jupyter lab \
            --ip=0.0.0.0 \
            --port=8889 \
            --ServerApp.token='"$USER_PASS"' \
            --notebook-dir="/" \
            --preferred-dir="$HOME" \
            --no-browser \
    fi' \
    > "${LOG_DIR}/services/jupyterlab.log" 2>&1 &
