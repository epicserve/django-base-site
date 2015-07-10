Install Pre-commit Hook
=======================

After you have setup your project by following the :doc:`setup-and-usage`, it's a
good idea to install the flake8 pre-commit hook, which will prevent you from
committing code with lint errors.

To install it, run the following in the root of your project::

$ flake8 --install-hook

Then run the following to figure out your virtualenv python location::

$ which python

Use path you just got to replace ``#!/usr/bin/env python`` with ``#!/path/to/virtualenvs/example/bin/python``
in ``.git/hooks/pre-commit``
