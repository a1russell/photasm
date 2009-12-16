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
    local('hg archive --type tgz /tmp/photosharing-%(release)s.tar.gz' % env)
    put('/tmp/photosharing-%(release)s.tar.gz' % env,
        '/tmp/photosharing-%(release)s.tar.gz' % env)
    with cd(env.project_root):
        sudo('tar -xzf /tmp/photosharing-%(release)s.tar.gz' % env)
    sudo('if [[ -d %(project_root)s/photosharing ]]; then '
         'mv %(project_root)s/photosharing '
         '%(project_root)s/photosharing-%(release)s.bak;'
         'fi' % env)
    sudo('mv %(project_root)s/photosharing-%(release)s '
         '%(project_root)s/photosharing' % env)
    sudo('if [[ -d %(project_root)s/photosharing-%(release)s.bak ]]; then '
         'mv %(project_root)s/photosharing-%(release)s.bak/settings_local.py '
         '%(project_root)s/photosharing/;'
         'rm -rf %(project_root)s/photosharing-%(release)s.bak;'
         'fi' % env)
    run('rm /tmp/photosharing-%(release)s.tar.gz' % env)
    local('rm /tmp/photosharing-%(release)s.tar.gz' % env)
    sudo('apache2ctl -k graceful')
