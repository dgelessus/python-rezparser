``rezparser``
=============

A pure Python library for parsing Macintosh Rez source files, which are used by the legacy ``Rez`` and ``DeRez`` tools to compile, modify and decompile Macintosh resource fork data.

Requirements
------------

Python 3.6 or later, as well as `PLY`__ (tested with version 3.10, but older and newer versions probably work too).

__ https://pypi.python.org/pypi/ply

Installation
------------

``rezparser`` is available `on PyPI`__ and can be installed using ``pip``: 

.. code-block:: sh

	python3 -m pip install rezparser

Alternatively you can install a local copy:

.. code-block:: sh

	python3 -m pip install -e .

__ https://pypi.python.org/pypi/rsrcfork

Changelog
---------

Version 1.0.0
`````````````

* Initial release version
