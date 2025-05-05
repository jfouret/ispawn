.. ispawn documentation master file, created by
   sphinx-quickstart on Fri Apr 25 17:06:31 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _index:

ispawn: Interactive Spawn Manager
========================================================

``ispawn`` acts as an **interactive spawn** manager. It simplifies creating and managing containerized development environments by introducing the concept of a **spawn**.

Forget manual Dockerfile crafting and complex setups. With ``ispawn``, you define *what* you need (base OS + services), and it handles the *how*, letting you focus purely on your interactive development and analysis tasks.

What is a **Spawn**?
--------------------
A **Spawn** is a ready-to-use, interactive development environment managed by ``ispawn``. It's built by layering components onto a base Docker image, resulting in a specialized **Spawn Image**. This image is then used to launch container instances, referred to as **Spawn Runs**.

The Spawn Image is constructed from three types of layers, each corresponding to Docker image layers defined by Dockerfile snippets:

#. **Base Image:**

   * The foundational layer used after ``FROM``.
   * Can be a simple OS (e.g., ``ubuntu:22.04``) or a complex, pre-configured environment (e.g., with specific R/Python versions and packages).

#. **Service Layers:**

   * Add the interactive tools you need (e.g., VSCode, RStudio, Jupyter).

   * ``ispawn`` provides curated Dockerfile snippets for each supported service, ensuring they are correctly installed and configured.

   * Selected via the ``--service`` option during ``ispawn build`` or ``ispawn run --build``.

#. **Setup Layers (Optional):**

   * Customize the environment further based on infrastructure needs (e.g., LDAP integration, proxy settings, custom certificates, additional packages).

   * Defined by user-provided Dockerfile snippets specified during ``ispawn setup`` (using ``--dockerfile-chunk-path``). These snippets are applied globally to all spawn images built by ``ispawn``.

.. note::
   Others things can be managed through ispawn such as the volume mounts, the entrypoint, the environment variables, the network settings, etc. See the documentation for more details.

Once the Spawn Image is built (e.g., ``ispawn-ubuntu:22.04_vscode_rstudio``), ``ispawn run`` launches it as a Spawn Run (a container), making the services accessible via HTTPS through the integrated Traefik proxy (e.g., ``https://myenv-vscode.ispawn.localhost``).

Core Features:
--------------

*   **🚀 Quick Setup & Launch:** Get started with a single ``ispawn setup`` command, then launch full environments with ``ispawn run``.
*   **🔧 Multiple Interactive Services:** Combine VSCode, RStudio, and Jupyter/JupyterLab/JupyterHub within a single spawn.
*   **🔒 Secure Browser Access:** Automatic HTTPS setup via Traefik for all services, accessible through predictable hostnames (e.g., ``myenv-vscode.ispawn.localhost``).
*   **📁 Volume Mapping & Data Persistence:** Automatically maps home directories and manages persistent storage within the spawn for service configurations and user data (VSCode settings/extensions, RStudio history, Jupyter configs).
*   **🔄 Spawn Lifecycle Management:** Simple commands (``run``, ``stop``, ``list``, ``remove``) to manage your spawns. (Note: `start` is not currently a command).
*   **🛠️ Global Build Customization:** Define custom Dockerfile snippets, environment variables, and entrypoint scripts during ``ispawn setup`` to tailor *all* future spawn image builds (e.g., install custom packages, set proxies).
*   **👥 Access Control:** Restrict RStudio access based on user groups within the spawn.
*   **💾 Image Management:** Build, list, and remove the enriched Docker images used for your spawns.

Explore the documentation to learn how to install, configure, and use ``ispawn``.

.. toctree::
   :maxdepth: 3

   manual
   cli
   api
