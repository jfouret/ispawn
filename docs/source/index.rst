.. ispawn documentation master file, created by
   sphinx-quickstart on Fri Apr 25 17:06:31 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _index:

ispawn: Interactive Spawn Manager for Containerized Development Environments
========================================================

``ispawn`` acts as an **i**nteractive **spawn** manager, applying a service layer onto Docker containers to automate the creation and management of complex, multi-service development environments. Forget manual Dockerfile crafting and complex setups for individual tools.

With ``ispawn``, you can instantly launch environments containing services like VSCode, RStudio, and Jupyter (or variants like JupyterLab/JupyterHub), all accessible securely via HTTPS in your web browser thanks to an integrated Traefik reverse proxy. It streamlines the entire lifecycle, letting you focus purely on your interactive development and analysis tasks.

Core Features:
--------------

*   **🚀 Quick Setup & Launch:** Get started with a single ``ispawn setup`` command, then launch full environments with ``ispawn run``.
*   **🔧 Multiple Interactive Services:** Run VSCode, RStudio, and Jupyter/JupyterLab/JupyterHub combinations within a single container.
*   **🔒 Secure Browser Access:** Automatic HTTPS setup via Traefik for all services, accessible through predictable hostnames (e.g., ``myenv-vscode.ispawn.localhost``).
*   **📁 Volume Mapping & Data Persistence:** Automatically maps home directories and manages persistent, isolated storage for each service's configuration and user data (VSCode settings/extensions, RStudio history, Jupyter configs).
*   **🔄 Container Lifecycle Management:** Simple commands (``run``, ``stop``, ``start``, ``list``, ``remove``) to manage your development containers.
*   **🛠️ Global Build Customization:** Define custom Dockerfile snippets, environment variables, and entrypoint scripts during setup to tailor *all* future image builds (e.g., install custom packages, set proxies).
*   **👥 Access Control:** Restrict RStudio access based on user groups within the container.
*   **💾 Image Management:** Build, list, and remove ispawn-managed service images.

Explore the documentation to learn how to install, configure, and use ``ispawn``.

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   usage
   troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Reference

   cli
   api

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
