
.. _using-vagrant:

Using Vagrant
=============

.. warning::

  Vagrant support has been deprecated and is no longer tested and will eventually be removed.

If you want to try out the ``django-base-site`` using Vagrant then you first
need to `install vagrant <http://docs.vagrantup.com/v1/docs/getting-started/index.html#install_vagrant>`_
of course. Then you can do the following to get things running.

::

    $ TARGET_DIR=~/Sites/ BRANCH=master PROJECT_NAME=example
    $ cd $TARGET_DIR
    $ curl -L "https://github.com/epicserve/django-base-site/archive/$BRANCH.zip" | tar zx -C $TARGET_DIR && mv "django-base-site-$BRANCH" $PROJECT_NAME
    $ cd $PROJECT_NAME
    $ vagrant up

After running ``vagrant up`` you'll need to wait (~5 minutes) while your new
Vagrant box is provisioned.

When it has finished provisioning your Vagrant box you should be able to run
``vagrant ssh`` to ssh to your new box. From there you can run ``drs`` to start
the Django runserver. You should now have the django development server running
in your Vagrant box. You can now open http://127.0.0.1:8000 in your local web
browser and you should be able to see the message, "You've successfully setup
a Django base site. Start Coding!".

Now you can just edit your ``django-base-site`` files locally in the ``~/Sites
/example`` directory and Django's runserver that's running in the
Vagrant box will detect any changes that are made.
