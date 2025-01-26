# Install VS Code Server
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  curl \
  && curl -fsSL https://code-server.dev/install.sh | sh \
  && rm -rf /var/lib/apt/lists/*
