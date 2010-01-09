from fabric.api import *


def deploy():
    """\
    Deploy the latest version of the site to the servers.
    
    """
    # Options for specifying env requirements:
    # In ~/.fabricrc: hosts = host1,host2
    # Command line, per task: fab deploy:hosts="host1;host2"
    # Command line, globally: fab --hosts host1,host2 deploy 
    require('hosts')
    require('project_root')
    import time
    env.release = time.strftime('%Y%m%d%H%M%S')
    local('hg archive --type tgz /tmp/photasm-%(release)s.tar.gz' % env)
    put('/tmp/photasm-%(release)s.tar.gz' % env,
        '/tmp/photasm-%(release)s.tar.gz' % env)
    with cd(env.project_root):
        sudo('tar -xzf /tmp/photasm-%(release)s.tar.gz' % env)
    sudo('if [[ -d %(project_root)s/photasm ]]; then '
         'mv %(project_root)s/photasm '
         '%(project_root)s/photasm-%(release)s.bak;'
         'fi' % env)
    sudo('mv %(project_root)s/photasm-%(release)s '
         '%(project_root)s/photasm' % env)
    sudo('if [[ -d %(project_root)s/photasm-%(release)s.bak ]]; then '
         'mv %(project_root)s/photasm-%(release)s.bak/settings_local.py '
         '%(project_root)s/photasm/;'
         'rm -rf %(project_root)s/photasm-%(release)s.bak;'
         'fi' % env)
    sudo('chown -R root:www-admin %(project_root)s/photasm' % env)
    sudo('chmod -R g+w %(project_root)s/photasm' % env)
    run('rm /tmp/photasm-%(release)s.tar.gz' % env)
    local('rm /tmp/photasm-%(release)s.tar.gz' % env)
    sudo('apache2ctl -k graceful')
