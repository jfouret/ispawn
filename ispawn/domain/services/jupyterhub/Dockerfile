# Check if jupyterhub is already in PATH, if not install it using micromamba
RUN which jupyterhub > /dev/null 2>&1 || ( \
    export MAMBA_ROOT_PREFIX=/opt/conda \
    && which micromamba > /dev/null 2>&1 || ( \
        tmpdir=$(mktemp -d) \
        && cd $tmpdir \
        && . /etc/environment \
        && wget -q https://github.com/mamba-org/micromamba-releases/releases/download/2.0.5-0/micromamba-linux-64.tar.bz2 \
        && tar -xjf micromamba-linux-64.tar.bz2 \
        && rm micromamba-linux-64.tar.bz2 \
        && chmod +x bin/micromamba \
        && mv bin/micromamba /usr/local/bin/micromamba \
        && cd .. \
        && rm -r $tmpdir \
    ) \
    && mkdir -p /opt/conda \
    && chmod 755 /opt/conda \
    && . /etc/environment \
    && micromamba create -y -n jupyterhub_ispawn -c conda-forge jupyterhub jupyterlab \
    && micromamba clean -ya \
)
