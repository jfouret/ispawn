.. _usage:

Usage
=====

Setup
-----

Before using ispawn for the first time, you need to set up the environment. This command initializes necessary configurations and sets up the Traefik reverse proxy if needed.

.. code-block:: bash

   ispawn setup

This will create configuration files, typically in ``~/.ispawn`` (user mode) or ``/etc/ispawn`` (system mode), depending on the installation.

Quick Start
-----------

1.  **Run a container** with default services (VSCode, RStudio, Jupyter):

    .. code-block:: bash

       ispawn run --name mydev --base ubuntu:22.04 --build

    *   ``--name mydev``: Assigns a name to your container.
    *   ``--base ubuntu:22.04``: Specifies the base Docker image to use. ispawn will build a new image on top of this, adding the requested services. If an image like ``ispawn/ubuntu:22.04`` doesn't exist locally, it will be built automatically.

2.  **Access your services** through your browser:

    ispawn uses a Traefik reverse proxy to provide secure HTTPS access to services via subdomains based on the container name. By default, these are under ``.ispawn.localhost``.

    *   VSCode:   ``https://mydev-vscode.ispawn.localhost``
    *   RStudio:  ``https://mydev-rstudio.ispawn.localhost``
    *   Jupyter:  ``https://mydev-jupyter.ispawn.localhost``

    You might need to accept self-signed certificates the first time you connect.

Building Images Explicitly
--------------------------

While ``ispawn run`` can build images implicitly using the ``--build`` flag, you can also build them explicitly using ``ispawn build``. This is useful for pre-building images or customizing the included services.

.. code-block:: bash

   # Build an image based on ubuntu:22.04 with only RStudio and JupyterLab
   ispawn build --base ubuntu:22.04 --services rstudio jupyterlab

   # Run a container using the pre-built image
   ispawn run --name analysis-env --base ubuntu:22.04 --services rstudio jupyterlab

.. note::
   Image are specifically build for each combination of services with a base image. 
   This means that if you build a base image with RStudio and JupyterLab, and then try to run a container with only RStudio, it will not work (or be rebuilt with the flag ``--build``). 

Build Customization
-------------------

You can customize how images are built by providing additional files during the initial ``ispawn setup`` command. These customizations apply globally to all subsequent builds.

*   **Environment File** (``--env-chunk-path``):
    *   A file containing environment variables (e.g., ``KEY=value`` pairs).
    *   These variables are added to ``/etc/environment`` within all built containers.
    *   Useful for setting global environment variables like proxy settings.

    *Example ``env.txt``:*

    .. code-block:: text

        CUSTOM_VAR=value
        PROXY_SERVER=proxy.company.com

*   **Dockerfile Chunk** (``--dockerfile-chunk-path``):
    *   A snippet of valid Dockerfile commands.
    *   This snippet is inserted after the ispawn-generated Dockerfile during the build process.
    *   Allows installation of additional system packages (e.g LDAP libraries) or other build-time modifications.

    *Example ``custom.dockerfile``:*

    .. code-block:: dockerfile

        RUN apt-get update && apt-get install -y \
            custom-package \
            another-package

*   **Entrypoint Script** (``--entrypoint-chunk-path``):
    *   A shell script.
    *   This script is executed as part of the container's entrypoint when the container starts.
    *   Useful for performing runtime configuration or setup tasks (e.g LDPA user config).

    *Example ``startup.sh``:*

    .. code-block:: bash

        #!/bin/bash
        echo "Configuring system at runtime..."
        custom-setup-command

To apply these during setup:

.. code-block:: bash

   ispawn setup --env-chunk-path env.txt --dockerfile-chunk-path custom.dockerfile --entrypoint-chunk-path startup.sh

Access Control
--------------

RStudio Group Access
~~~~~~~~~~~~~~~~~~~~

Access to the RStudio service can be restricted to members of a specific system group.

*   By default, only the user who runs the ``ispawn run`` command can access the RStudio instance within the container.
*   Use the ``--group <group_name>`` option with ``ispawn run`` to specify a group whose members should be granted access.
*   Users attempting to log in to RStudio must belong to this group *within the container's environment*. This often mirrors the host system's groups if user IDs are mapped correctly.

Example restricting access to the ``data-scientists`` group:

.. code-block:: bash

   ispawn run --name analysis --base ubuntu:22.04 --group data-scientists

Data Persistence
----------------

ispawn ensures that user data and configurations for each service within a container persist across container restarts and removals. It achieves this by mounting specific host directories into the container at the correct locations.

Service-Specific Volumes
~~~~~~~~~~~~~~~~~~~~~~~~

Each service has designated directories within the container that are backed by volumes on the host machine:

1.  **RStudio**:
    *   ``~/.local/share/rstudio``: Stores RStudio user settings, history, etc.
    *   Mounted to persist user preferences and state.

2.  **Jupyter**:
    *   ``~/.jupyter``: Jupyter configuration files.
    *   ``~/.ipython``: IPython history, profiles, and settings.
    *   Maintains notebook settings, kernels, and history.

3.  **VSCode**:
    *   ``~/.vscode``: VSCode user settings and configurations.
    *   ``~/.config/Code``: VSCode extensions cache and workspace state.
    *   Preserves installed extensions, UI state, and user preferences.

Volume Organization on Host
~~~~~~~~~~~~~~~~~~~~~~~~~~~

*   ispawn manages these volumes within its configuration directory (e.g., ``~/.ispawn/user/ispawn/volumes/``).
*   Each container gets its own dedicated subdirectory under ``volumes/``, named after the container (e.g., ``mydev/``).
*   Inside the container's directory, service-specific data is further isolated (e.g., ``mydev/rstudio/share/``, ``mydev/jupyter/jupyter/``).
*   This structure ensures data isolation between containers and services.

*Example host directory structure:*

.. code-block:: text

    ~/.ispawn/user/ispawn/volumes/
    └── mydev/
        ├── rstudio/
        │   └── share/        # Maps to ~/.local/share/rstudio in container
        ├── jupyter/
        │   ├── jupyter/      # Maps to ~/.jupyter in container
        │   └── ipython/      # Maps to ~/.ipython in container
        └── vscode/
            ├── vscode/       # Maps to ~/.vscode in container
            └── config/       # Maps to ~/.config/Code in container

Data persists even if the container is stopped and removed (using ``ispawn stop`` and ``ispawn remove``). A new container started with the same name will reuse the existing volume directory.

Managing Containers
-------------------

List running or all ispawn containers:

.. code-block:: bash

   # List running containers
   ispawn list

   # List all containers (including stopped)
   ispawn list --all

Stop a running container:

.. code-block:: bash

   ispawn stop mydev

Remove a stopped container (associated volumes are kept unless ``--remove-volumes`` is used):

.. code-block:: bash

   ispawn remove mydev

Managing Images
---------------

List ispawn-managed Docker images:

.. code-block:: bash

   ispawn image list

Remove an ispawn-managed image:

.. code-block:: bash

   ispawn image remove ispawn/ubuntu:22.04_vscode_rstudio_jupyter
