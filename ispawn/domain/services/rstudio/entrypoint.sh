#!/bin/bash

# Configure RStudio Server
echo "[$(date)] Configuring RStudio server..."
RSTUDIO_CONFIG_LINE="auth-required-user-group=${REQUIRED_GROUP}"
RSTUDIO_CONFIG_FILE="/etc/rstudio/rserver.conf"
# Ensure the line is present in the config file, but don't add it if it's already there
grep -qFx "${RSTUDIO_CONFIG_LINE}" "${RSTUDIO_CONFIG_FILE}" || echo "${RSTUDIO_CONFIG_LINE}" >> "${RSTUDIO_CONFIG_FILE}"

# Start RStudio Server
echo "[$(date)] Starting RStudio server..."
mkdir -p "${LOG_DIR}/rstudio"
LOG_FILE="${LOG_DIR}/services/rstudio.log"
if [ -f "${LOG_FILE}" ]; then
    i=1
    while [ -f "${LOG_FILE}.${i}" ]; do
        i=$((i + 1))
    done
    mv "${LOG_FILE}" "${LOG_FILE}.${i}"
fi
rstudio-server start > "${LOG_FILE}" 2>&1

