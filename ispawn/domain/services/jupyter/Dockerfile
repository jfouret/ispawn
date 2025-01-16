
# Set micromamba base prefix to a shared location and create directory with appropriate permissions
ENV MAMBA_ROOT_PREFIX=/opt/conda
# Check if jupyter and micromamba are already in PATH
RUN which jupyter > /dev/null 2>&1 && which micromamba > /dev/null 2>&1 || ( \
      tmpdir=$(mktemp -d) \
      && cd $tmpdir \
      && wget -q https://github.com/mamba-org/micromamba-releases/releases/download/2.0.5-0/micromamba-linux-$(uname -m | sed 's/x86_//g').tar.bz2 \
      && tar -xvj micromamba-linux-64.tar.bz2 \
      && rm micromamba-linux-64.tar.bz2 \
      && chmod +x bin/micromamba \
      && mv bin/micromamba /usr/local/bin/micromamba \
      && cd .. \
      && rm -r $tmpdir \
    )

RUN which jupyter > /dev/null 2>&1 || ( \
      mkdir -p /opt/conda && chmod 755 /opt/conda \
      && micromamba create -y -n jupyter_ispawn -c conda-forge jupyter \
      && micromamba clean -ya \
    )
