#!/bin/bash

# Start RStudio Server
echo "[$(date)] Starting RStudio server..."
mkdir -p "${LOG_DIR}/rstudio"
rstudio-server start > "${LOG_DIR}/services/rstudio.log" 2>&1

