
# Check if jupyter and micromamba are already in PATH

RUN which jupyter > /dev/null 2>&1 && which micromamba > /dev/null 2>&1 || ( \
      # makr tmpkir and change directory to it
      tmpdir=$(mktemp -d) \
      && cd $tmpdir \
      && curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba \
      && mv bin/micromamba /usr/local/bin/micromamba \
      && cd .. \
      && rm -r $tmpdir \
    )

RUN which jupyter > /dev/null 2>&1 || ( \
      micromamba create -y -n jupyter_ispawn -c conda-forge jupyter \
      && micromamba clean -ya \
    )
 
