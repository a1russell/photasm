from fabric.api import (
    cd,
    env,
    local,
    put,
    require,
    run,
    sudo,
)


env.project_name = 'photasm'
env.project_root = '/usr/local/webapps/'


def deploy():
    """\
    Deploy the latest version of the site to the servers.

    """
    # Options for specifying env requirements:
    # Command line, per task: fab deploy:hosts="host1;host2"
    # Command line, globally: fab --hosts host1,host2 deploy
    require('hosts')
    require('project_root')  # e.g. /usr/local/webapps/
    require('project_name')
    import time
    env.release = time.strftime('%Y%m%d%H%M%S')
    local('hg archive --type tgz '
          '/tmp/%(project_name)s-%(release)s.tar.gz' % env)
    put('/tmp/%(project_name)s-%(release)s.tar.gz' % env,
        '/tmp/%(project_name)s-%(release)s.tar.gz' % env)
    with cd(env.project_root):
        sudo('tar -xzf /tmp/%(project_name)s-%(release)s.tar.gz' % env)
    sudo('if [[ -d %(project_root)s/%(project_name)s ]]; then '
         'mv %(project_root)s/%(project_name)s '
         '%(project_root)s/%(project_name)s-%(release)s.bak;'
         'fi' % env)
    sudo('mv %(project_root)s/%(project_name)s-%(release)s '
         '%(project_root)s/%(project_name)s' % env)
    sudo('if [[ -f %(project_root)s/%(project_name)s-%(release)s.bak/'
         'settings_local.py ]]; then '
         'mv %(project_root)s/%(project_name)s-%(release)s.bak/'
         'settings_local.py '
         '%(project_root)s/%(project_name)s/;'
         'else '
         'cp %(project_root)s/%(project_name)s/settings_local.py.template '
         '%(project_root)s/%(project_name)s/settings_local.py; '
         'fi' % env)
    sudo('if [[ -d %(project_root)s/%(project_name)s-%(release)s.bak ]]; '
         'then '
         'rm -rf %(project_root)s/%(project_name)s-%(release)s.bak;'
         'fi' % env)
    sudo('chown -R root:www-admin %(project_root)s/%(project_name)s' % env)
    sudo('chmod -R g+w %(project_root)s/%(project_name)s' % env)
    run('rm /tmp/%(project_name)s-%(release)s.tar.gz' % env)
    local('rm /tmp/%(project_name)s-%(release)s.tar.gz' % env)
    sudo('if ( ps -ef | grep apache2 | grep -v grep ); then '
         'apache2ctl -k graceful; fi')
