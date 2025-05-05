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

1.  **Run a spawn** with default services (VSCode, RStudio, Jupyter):

    .. code-block:: bash

       ispawn run --name mydev --base ubuntu:22.04 --build

    *   ``--name mydev``: Assigns a unique name to your spawn run.
    *   ``--base ubuntu:22.04``: Specifies the base Docker image. ispawn looks for an existing spawn image (e.g., ``ispawn-ubuntu:22.04_vscode_rstudio_jupyter``) and runs it if available.
    *   ``--build``: If the required spawn image (e.g., ``ispawn-ubuntu:22.04_vscode_rstudio_jupyter``) doesn't exist, build it automatically before running the spawn.

2.  **Access your services** through your browser:

    ispawn uses a Traefik reverse proxy to provide secure HTTPS access to services via subdomains based on the spawn run name and sevices. By default, these are under ``.ispawn.localhost``.

    *   VSCode:   ``https://mydev-vscode.ispawn.localhost``
    *   RStudio:  ``https://mydev-rstudio.ispawn.localhost``
    *   Jupyter:  ``https://mydev-jupyter.ispawn.localhost``

    You might need to accept self-signed certificates the first time you connect.

Building Spawn Images Explicitly
--------------------------------

While ``ispawn run`` can build spawn images implicitly using the ``--build`` flag, you can also build them explicitly using ``ispawn build``. This is useful for pre-building images or customizing the included services.

.. code-block:: bash

   # Build an image based on ubuntu:22.04 with only RStudio and JupyterLab
   ispawn build --base ubuntu:22.04 --service rstudio --service jupyterlab

   # Run a spawn using the pre-built image
   ispawn run --name analysis-env --base ubuntu:22.04 --service rstudio --service jupyterlab

.. note::
   Spawn Images are specifically built for each unique combination of a base image and selected services.
   This means if you build an image with RStudio and JupyterLab, you cannot directly run a spawn requesting only RStudio from that *exact* image. You would need to either build a new image specifically for RStudio or use the ``--build`` flag with ``ispawn run`` to create it on the fly.

Build Customization
-------------------

You can customize how images are built by providing additional files during the initial ``ispawn setup`` command. These customizations apply globally to all subsequent builds.

*   **Environment File** (``--env-chunk-path``):
    *   A file containing environment variables (e.g., ``KEY=value`` pairs).
    *   These variables are added to ``/etc/environment`` within all built spawn images.
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
    *   This script is executed as part of the spawn's entrypoint when the spawn starts.
    *   Useful for performing runtime configuration or setup tasks (e.g., LDAP user config).

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

*   By default, only the user who runs the ``ispawn run`` command can access the RStudio instance within the spawn.
*   Use the ``--group <group_name>`` option with ``ispawn run`` to specify a group whose members should be granted access.
*   Users attempting to log in to RStudio must belong to this group *within the spawn's environment*. This often mirrors the host system's groups if user IDs are mapped correctly.

Example restricting access to the ``data-scientists`` group:

.. code-block:: bash

   ispawn run --name analysis --base ubuntu:22.04 --group data-scientists

Data Persistence
----------------

ispawn ensures that user data and configurations for each service within a spawn persist across spawn restarts and removals. It achieves this by mounting specific host directories into the spawn at the correct locations.

Service-Specific Volumes
~~~~~~~~~~~~~~~~~~~~~~~~

Each service has designated directories within the spawn that are backed by volumes on the host machine:

1.  **RStudio**: ``~/.local/share/rstudio`` (stores settings, history, etc.)
2.  **Jupyter**: ``~/.jupyter`` (config), ``~/.ipython`` (history, profiles)
3.  **VSCode**: ``~/.vscode`` (settings), ``~/.config/Code`` (extensions, state)

Volume Organization on Host
~~~~~~~~~~~~~~~~~~~~~~~~~~~

*   ispawn manages these volumes within its configuration directory (e.g., ``~/.ispawn/user/ispawn/volumes/``).
*   Each spawn run gets its own dedicated subdirectory under ``volumes/``, named after the spawn run name (e.g., ``mydev/``).
*   Inside the spawn run's directory, service-specific data is further isolated (e.g., ``mydev/rstudio/share/``, ``mydev/jupyter/jupyter/``).
*   This structure ensures data isolation between services of distrinct spawn runs.

*Example host directory structure:*

.. code-block:: text

    ~/.ispawn/user/ispawn/volumes/
    └── mydev/
        ├── rstudio/
        │   └── share/        # Maps to ~/.local/share/rstudio in spawn
        ├── jupyter/
        │   ├── jupyter/      # Maps to ~/.jupyter in spawn
        │   └── ipython/      # Maps to ~/.ipython in spawn
        └── vscode/
            ├── vscode/       # Maps to ~/.vscode in spawn
            └── config/       # Maps to ~/.config/Code in spawn

Data persists even if the spawn run is stopped and removed (using ``ispawn stop`` and ``ispawn remove``). A new spawn started with the same name will reuse the existing volume directory.

Managing Spawns images and runs
-------------------------------

List started spawn run:

.. code-block:: bash

   # List running spawns
   ispawn list

* List all spawns (including stopped ones)

Stop a running spawn:

.. code-block:: bash

   ispawn stop ispawn-mydev

Remove a stopped spawn (associated volumes are kept):

..note:: The prefix is needed here (what is expected is the container name/not the spawn name).

.. code-block:: bash

   ispawn remove ispawn-mydev

   # Remove all stopped spawns
   ispawn remove --all

Managing Spawn Images
---------------------

List ispawn-managed Docker images (the enriched images used for spawns):

.. code-block:: bash

   ispawn image list

Remove an ispawn-managed image (specify by tag or ID):

.. code-block:: bash

   ispawn image remove ispawn-ubuntu:22.04_vscode_rstudio_jupyter
