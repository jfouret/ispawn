#!/bin/bash

# Start VS Code Server
sudo -u "$USER_NAME" \
  PASSWORD="$USER_PASS" code-server \
    --bind-addr 0.0.0.0:8842 \
    --auth password \
    > "${LOG_DIR}/services/vscode.log" 2>&1 &

