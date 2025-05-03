Usage
=====

Setup
-----

Before using ispawn, you need to set up the environment:

.. code-block:: bash

   ispawn setup

This will create a configuration file in either ``~/.ispawn`` (user mode) or ``/etc/ispawn`` (system mode).

Building Images
--------------

To build a Docker image with specific services:

.. code-block:: bash

   ispawn build -b ubuntu:22.04 -s rstudio -s jupyterlab

Running Containers
-----------------

To run a container with the built image:

.. code-block:: bash

   ispawn run -n my-container -b ispawn/ubuntu:22.04 -v /path/to/data

Managing Containers
------------------

List running containers:

.. code-block:: bash

   ispawn list

Stop a container:

.. code-block:: bash

   ispawn stop my-container

Remove a container:

.. code-block:: bash

   ispawn remove my-container

Managing Images
--------------

List available images:

.. code-block:: bash

   ispawn image list

Remove an image:

.. code-block:: bash

   ispawn image remove ispawn/ubuntu:22.04
