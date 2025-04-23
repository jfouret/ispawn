
# Check if jupyter is already in PATH, if not install it using micromamba
RUN which jupyter > /dev/null 2>&1 || ( \
    export MAMBA_ROOT_PREFIX=/opt/conda \
    && which micromamba > /dev/null 2>&1 || ( \
      tmpdir=$(mktemp -d) \
      && cd $tmpdir \
      && . /etc/environment \
      && wget -q https://github.com/mamba-org/micromamba-releases/releases/download/${MAMBA_VERSION}/micromamba-${ARCH}.tar.bz2 \
      && tar -xjf micromamba-${ARCH}.tar.bz2 \
      && rm micromamba-${ARCH}.tar.bz2 \
      && chmod +x bin/micromamba \
      && mv bin/micromamba /usr/local/bin/micromamba \
      && cd .. \
      && rm -r $tmpdir \
    )

RUN which jupyter > /dev/null 2>&1 || ( \
  export MAMBA_ROOT_PREFIX=/opt/conda  \
  mkdir -p /opt/conda && chmod 755 /opt/conda \
    && . /etc/environment \
    && micromamba create -y -n jupyter_ispawn -c conda-forge jupyter \
    && micromamba clean -ya \
  )
