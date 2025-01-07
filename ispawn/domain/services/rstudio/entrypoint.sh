#!/bin/bash

# Start RStudio Server
echo "[$(date)] Starting RStudio server..."
mkdir -p "${LOG_DIR}/rstudio"
rstudio-server start > "${LOG_DIR}/rstudio/rstudio.log" 2>&1

