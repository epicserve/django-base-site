Django Base Site
================


About
-----

The Django Base Site is a skeleton base site that can be used to jumpstart any
new Django site. `Brent O'Connor <http://www.epicserve.com/>`_ created it so
he could use it personally to jumpstart any of his new Django projects. Please
feel free to fork this project and adapt it to your own personal taste. To
setup a new website just follow the `setup instructions
<https://github.com/epicserve/django-base-site/blob/master/docs/usage-and-
setup.rst>`_.

Using Vagrant
-------------

If you want to try out the `django-base-site` using Vagrant then you first
need to [install vagrant](http://docs.vagrantup.com/v1/docs/getting-
started/index.html#install_vagrant) of course. Then you can do the following
to get things running.

    $ cd ~/Sites/
    $ git clone git://github.com/epicserve/django-base-site.git
    $ cd django-base-site
    $ vagrant up
    $ vagrant ssh
    $ workon django-base-site
    $ drs

You should now have the django development server running in your Vagrant
virtual machine. You can now open
[http://127.0.0.1:8000](http://127.0.0.1:8000) in your local web browser and
you should be able to see the message, "You've successfully setup a Django
base site. Start Coding!".

Now you can just edit your `django-base-site` files locally in the `~/Sites
/django-base-site` directory and Django's runserver that's running in the
virtual machine will detect any changes that are made.
