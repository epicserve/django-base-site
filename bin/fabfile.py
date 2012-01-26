from fabric.api import env, run, cd, local, sudo, execute, roles, settings, task
from fabric.colors import green
from django.conf import settings as dja_settings

env.roledefs = {
    'db': ['db.example.com'],
    'web': ['appserv.example.com'],
}
env.code_dir = '/srv/sites/example'
env.virtualenv = '/usr/local/virtualenvs/example'
env.django_project_root = dja_settings.DJANGO_PROJECT_ROOT
env.django_settings_module = 'config.settings'
env.nginx_confs = (
    'example.com.conf',
)
env.upstart_confs = (
    'celeryd_example.com.conf',
    'gunicorn_example.com.conf',
)
env.cron_config_files = (
    'example_task',
)


@task
@roles('db')
def sync_database():
    "Refreshes the local copy of the database passed in by pulling it from the server specified"

    params = {'db_name': dja_settings.DATABASE_NAME}
    params.update(env)

    # dump the database and compress it on the remote server
    run('/usr/local/pgsql/bin/pg_dump %(db_name)s | gzip > /tmp/%(db_name)s.sql.gz' % params)

    # securely copy the compressed file to local temporary storage
    local('scp %(host)s:/tmp/%(db_name)s.sql.gz /tmp/' % params)

    print('Creating database...[%s]' % green(params['db_name'], True))

    # drop it if it exists and re-create
    local('psql -d template1 -c "drop database if exists %(db_name)s;" && createdb %(db_name)s -O %(db_name)s' % params)

    # unzip the temp file and restore
    local('gunzip -f /tmp/%(db_name)s.sql.gz' % params)
    local('cat /tmp/%(db_name)s.sql | psql %(db_name)s' % params)
    local('rm /tmp/%(db_name)s.sql' % params)
    run('rm /tmp/%(db_name)s.sql.gz' % params)


@task
@roles('web')
def sync_media():
    "Pulls and syncs photos from the production server your local dev instance"
    local("rsync -avz -e ssh %s:%s/media/ %s/media/" % (env.host, env.code_dir, env.django_project_root))


@task
@roles('web')
def update_nginx_configs(enable_config=False):
    "Update the nginx config files"
    for config_file in env.nginx_confs:
        local_file = "%s/config/nginx/%s" % (env.django_project_root, config_file)
        remote_tmp_file = '/tmp/%s' % config_file
        remote_file = "/etc/nginx/sites-available/%s" % config_file
        local("scp %s %s:%s" % (local_file, env.host, remote_tmp_file))
        sudo("chown root:root %s" % remote_tmp_file)
        sudo("mv %s %s" % (remote_tmp_file, remote_file))
        if enable_config:
            with cd('/etc/nginx/sites-enabled/'):
                sudo('ln -nsf ../sites-available/%s' % config_file)
    sudo("nginx -s reload")


@task
@roles('web')
def update_upstart_configs():
    "Update all the upstart configs for gunicorn"
    for config_file in env.upstart_confs:
        local_file = "%s/config/upstart/%s" % (env.django_project_root, config_file)
        remote_tmp_file = '/tmp/%s' % config_file
        remote_file = "/etc/init/%s" % config_file
        local("scp %s %s:%s" % (local_file, env.host, remote_tmp_file))
        sudo("chown root:root %s" % remote_tmp_file)
        sudo("mv %s %s" % (remote_tmp_file, remote_file))
    execute(reload_site)


@task
@roles('web')
def update_cron_configs():
    "Update all the cron configs"
    for config_file in env.cron_config_files:
        local_file = "%s/config/cron/%s" % (env.django_project_root, config_file)
        remote_tmp_file = '/tmp/%s' % config_file
        remote_file = "/etc/cron.d/%s" % config_file
        local("scp %s %s:%s" % (local_file, env.host, remote_tmp_file))
        sudo("chown root:root %s" % remote_tmp_file)
        sudo("mv %s %s" % (remote_tmp_file, remote_file))


@task
@roles('web')
def push():
    "Push new code and pull on all hosts"
    local('git push origin master')
    with cd(env.code_dir):
        sudo('git pull', user='deploy')


@task
@roles('web')
def update_requirements():
    "Update requirements in the virtualenv."
    sudo("%s/bin/pip install -r %s/config/requirements/base.txt -r %s/config/requirements/production.txt" % (env.virtualenv, env.code_dir, env.code_dir), user='deploy')


@task
@roles('web')
def migrate(app=None):
    """Run the migrate task
    Usage: fab migrate:app_name"""
    if app:
        sudo("source %s/bin/activate; django-admin.py migrate %s --settings=%s" % (env.virtualenv, app, env.django_settings_module), user='deploy')
    else:
        sudo("source %s/bin/activate; django-admin.py migrate --settings=%s" % (env.virtualenv, env.django_settings_module), user='deploy')


@task
@roles('web')
def reload_site():
    "Makes the site reload"
    for config_file in env.upstart_confs:
        config_file = config_file[:config_file.rfind('.')]
        with cd("/etc/init/"):
            with settings(warn_only=True):
                result = sudo("restart %s" % config_file)
            if result.failed:
                sudo("start %s" % config_file)


@task
@roles('web')
def deploy():
    "Deploy from the current local dev site to production"
    push()
    update_requirements()
    migrate()
    reload_site()
