.. _troubleshooting:

Troubleshooting
===============

Common Issues
-------------

1.  **Certificate Errors**
    *   For local development, ensure your system trusts the generated certificates.
    *   For remote access, verify your SSL certificates are valid.

2.  **Port Conflicts**
    *   Ensure ports 80/443 are available for traefik.
    *   Check for other services using required ports.

3.  **Container Access**
    *   Verify the container is running with ``ispawn list``.
    *   Check your ``/etc/hosts`` file has the correct entries.
    *   Ensure your browser accepts the SSL certificates.

4.  **RStudio Access Denied**
    *   Verify you belong to the required group if ``--group`` was used.
    *   Check the group name matches exactly.
    *   Use the ``groups`` command in the container or host to list your groups.

5.  **Data Persistence Issues**
    *   Check volume directory permissions (typically in ``~/.ispawn/user/ispawn/volumes/``).
    *   Verify service-specific subdirectories exist within the container's volume directory.
    *   Ensure proper overlay mounting order (ispawn handles this internally).

Getting Help
------------

*   Check the `GitHub Issues <https://github.com/jfouret/ispawn/issues>`_ for known problems or to report a new one.
*   For development-related questions, see the :ref:`contributing` guide.
