from fabric.api import cd, run, env, local

env.hosts = ['foo.example.com']
env.code_dir = '/var/www/project'
env.virtualenv = '/usr/local/virtualenvs/project'
env.django_settings_module = 'config.settings'


def push():
    "Push new code and pull on all hosts"
    local('git push origin master')
    with cd(env.code_dir):
        run('git pull origin master')


def update_requirements():
    "Update requirements in the virtualenv."
    run("%s/bin/pip install -r %s/config/requirements.txt" % (env.virtualenv, env.code_dir))


def migrate(app=None):
    """Run the migrate task
    Usage: fab migrate:app_name"""
    if app:
        run("source %s/bin/activate; django-admin.py migrate %s --settings=%s" % (env.virtualenv, app, env.django_settings_module))
    else:
        run("source %s/bin/activate; django-admin.py migrate --settings=%s" % (env.virtualenv, env.django_settings_module))


def deploy():
    push()
    update_requirements()
    migrate()
    run("touch %s/config/apache/project.wsgi" % env.code_dir)
