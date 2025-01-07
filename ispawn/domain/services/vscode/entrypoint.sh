#!/bin/bash

# Start VS Code Server
sudo -u "$USERNAME" code-server \
    --bind-addr 0.0.0.0:8842 \
    --auth password \
    --password "$PASSWORD" \
    > "${LOG_DIR}/vscode/vscode.log" 2>&1 &

