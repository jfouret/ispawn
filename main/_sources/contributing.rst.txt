.. _contributing:

Contributing to ispawn
======================

This guide is for developers who want to contribute to ispawn. For user documentation, see the main documentation index.

Development Setup
-----------------

Requirements
~~~~~~~~~~~~

*   Python >=3.11
*   Docker
*   Poetry
*   Development dependencies: ``poetry install --with dev``

Project Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

    ispawn/
    ├── __init__.py
    ├── main.py         # CLI entrypoint using Click
    ├── domain/         # Core business logic, data models, and app service definitions
    │   ├── __init__.py
    │   ├── config.py     # Configuration models (InstallMode, CertMode, etc.)
    │   ├── container.py  # Container configuration logic
    │   ├── exceptions.py # Custom exceptions
    │   ├── image.py      # Image configuration logic (base image, services)
    │   └── services/     # Definitions for runnable applications (VSCode, RStudio, etc.)
    │       ├── jupyter/
    │       ├── jupyterhub/
    │       ├── jupyterlab/
    │       ├── rstudio/
    │       └── vscode/
    ├── services/       # Business operations and external integrations (Docker API, Config Mgmt)
    │   ├── __init__.py
    │   ├── config.py     # Configuration management (reading/writing config files)
    │   ├── container.py  # Container lifecycle management (run, stop, list, remove)
    │   └── image.py      # Image management (build, list, remove)
    ├── templates/      # Jinja2 templates for Dockerfiles, entrypoints, Traefik configs
    └── files/          # Static configuration files (e.g., Traefik dynamic providers)

Architecture
------------

Overview
~~~~~~~~

ispawn follows a layered architecture pattern with clear separation of concerns:

Domain Layer (``domain/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~

The domain layer contains the core business logic and data models. These are pure Python classes that don't depend on external services or frameworks.

Domain models are designed to be:

*   Independent of external services
*   Focused on business rules
*   Highly testable
*   Free of side effects

Service Layer (``services/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Services implement operations that often involve external systems or side effects:

Services are responsible for:

*   Integrating with external systems
*   Implementing complex operations
*   Managing resources
*   Handling errors and retries

Key Design Principles
~~~~~~~~~~~~~~~~~~~~~

1.  **Separation of Concerns**
    *   Domain models focus on business logic
    *   Services handle external integrations
    *   Commands coordinate operations

2.  **Dependency Direction**

    .. code-block:: text

        commands → services → domain

    *   Domain has no external dependencies
    *   Services depend on domain
    *   Commands depend on services and domain

3.  **Error Handling**
    *   Domain defines custom exceptions
    *   Services translate external errors
    *   Commands present errors to users

Testing
-------

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

    # Run unit tests
    pytest

    # Run with coverage
    pytest --cov=ispawn

    # Run integration tests
    pytest -m integration

    # Run end-to-end tests
    pytest -m e2e

Testing Strategy
~~~~~~~~~~~~~~~~

Tests are organized in multiple layers:

1.  **Unit Tests**
    *   Test individual components in isolation
    *   Mock external dependencies
    *   Focus on business logic

2.  **Integration Tests**
    *   Test interaction between components
    *   Use real Docker daemon
    *   Verify service integration

3.  **End-to-End Tests**
    *   Test complete workflows
    *   Simulate real user scenarios
    *   Verify system behavior

Contributing Guidelines
-----------------------

1.  Fork the repository
2.  Create a feature branch (``git checkout -b feature/amazing-feature``)
3.  Make your changes
4.  Add tests for your changes
5.  Run the test suite to ensure everything passes
6.  Commit your changes (``git commit -m 'Add amazing feature'``)
7.  Push to the branch (``git push origin feature/amazing-feature``)
8.  Create a Pull Request

Code Style
~~~~~~~~~~

*   Follow PEP 8 guidelines
*   Use type hints
*   Write docstrings for public functions
*   Keep functions focused and small
*   Add comments for complex logic

Pull Request Process
~~~~~~~~~~~~~~~~~~~~

1.  Update documentation for any changed functionality (including this ``contributing.rst`` guide if processes change).
2.  If adding new modules or significantly changing existing ones, ensure ``docs/source/api.rst`` is updated accordingly (or that auto-generation picks up the changes).
3.  Add tests for new features.
4.  Update ``CHANGELOG.md`` if applicable.
5.  Ensure CI passes all checks.
6.  Get review from maintainers.

Building the Documentation Locally
----------------------------------

The documentation is built using Sphinx. To build it locally:

1.  Ensure you have installed the development dependencies:

    .. code-block:: bash

       poetry install --with dev

2.  Navigate to the ``docs/`` directory:

    .. code-block:: bash

       cd docs

3.  Build the HTML documentation:

    .. code-block:: bash

       poetry run make html
       # Or on Windows:
       # poetry run .\make.bat html

The generated documentation will be available in ``docs/build/html/index.html``.

License
-------

This project is licensed under the Apache-2.0 License - see the ``LICENSE.txt`` file for details.
