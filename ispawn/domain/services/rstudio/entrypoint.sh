#!/bin/bash

# Configure RStudio Server
echo "[$(date)] Configuring RStudio server..."
echo "auth-required-user-group=${REQUIRED_GROUP}" >> /etc/rstudio/rserver.conf

# Start RStudio Server
echo "[$(date)] Starting RStudio server..."
mkdir -p "${LOG_DIR}/rstudio"
rstudio-server start > "${LOG_DIR}/services/rstudio.log" 2>&1
