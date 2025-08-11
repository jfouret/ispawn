#!/bin/bash

sudo -u "$USER_NAME" bash -s -- "$USER_PASS" "$LOG_DIR" <<'EOF'
  cd ~

  # If jupyter is not in the PATH, activate the micromamba environment
  if ! command -v jupyter > /dev/null 2>&1; then
    eval "$(micromamba shell hook --shell bash --root-prefix /opt/conda)"
    export MAMBA_ROOT_PREFIX=/opt/conda
    micromamba activate jupyter_ispawn
  fi

  mkdir -p $2/services

  jupyter notebook --ip=0.0.0.0 \
  --port=8888 \
  --ServerApp.token=$1 \
  --ServerApp.root_dir=/ \
  --FileContentsManager.preferred_dir=$HOME \
  --no-browser \
  --ServerApp.allow_root=True \
  --ServerApp.quit_button=False > "$2/services/jupyter.log" 2>&1 &
EOF

