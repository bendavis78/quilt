import os
from quilt.contrib import fs
from fabric.api import env

env.resources.nginx.conf_dir = '/etc/nginx'
env.resources.nginx.conf_owner = 'root'
env.resources.nginx.conf_group = 'root'
env.resources.nginx.www_root = '/var/www'
env.resources.nginx.www_user = 'www-data'
env.resources.nginx.www_group = 'www-data'

env.resources.nginx.site.conf_dir = '/etc/nginx/sites-available'
env.resources.nginx.site.symlink_dir = '/etc/nginx/sites-enabled'
env.resources.nginx.site.static_dirs = []
env.resources.nginx.site.internal_static_dirs = []

class Site(fs.File):
    template = 'site.conf'

    domain = None
    root = None
    owner = None
    group = None
    static_dirs = None
    internal_static_dirs = None
    upstreams = None
    aliases = None
    non_redirect_aliases = None
    conf_dir = None
    symlink_dir = None
    www_root = None
    
    def __init__(self, name, **kwargs):
        super(Site, self).__init__(name, **kwargs)
        if self.path is None or self.path == self.name:
            conf_dir = env.resources.nginx.site.conf_dir
            self.path = os.path.join(conf_dir, '{}.conf'.format(self.name))

    def clean(self):
        super(Site, self).clean()
        if not self.www_root:
            self.www_root = env.resources.nginx.www_root
        self.require('www_root', 'name')

    def ensure(self):
        nginx_conf_dir = fs.Directory(env.resources.nginx.conf_dir,
                                      owner=env.resources.nginx.conf_owner,
                                      group=env.resources.nginx.conf_group)
        nginx_conf_dir.ensure()
        conf_defaults = {
            'owner': nginx_conf_dir.owner,
            'group': nginx_conf_dir.group
        }

        super(Site, self).ensure()

        if self.owner is None:
            self.owner = conf_defaults['owner']

        if self.group is None:
            self.group = conf_defaults['group']
        
        nginx_user = env.resources.nginx.www_user
        nginx_group = env.resources.nginx.www_group
        fs.Directory(self.www_root, owner=nginx_user, group=nginx_group).ensure()

        if self.symlink_dir:
            symlink_dir = fs.Directory(self.symlink_dir, **conf_defaults)
            symlink_dir.ensure()
            conf_filename = os.path.split(self.path)[-1]
            symlink_path = os.path.join(symlink_dir.path, conf_filename)
            fs.Symlink(symlink_path, target=self.path, owner=self.owner, 
                    group=self.group).ensure()

        if not self.root:
            self.root = '{}/{}'.format(self.www_root, self.name)
        self.root = '/{}'.format(self.root.strip('/'))
        root_dir = fs.Directory(self.root, owner=nginx_user, group=nginx_group)
        root_dir.ensure()
        
        for i, dir in enumerate(self.static_dirs):
            dir = dir.strip('/')
            self.static_dirs[i] = dir
            dir_path = '{}/{}'.format(self.root, dir)
            static_dir = fs.Directory(dir_path, owner=root_dir.owner, group=root_dir.group)
            static_dir.ensure()

        for i, dir in enumerate(self.internal_static_dirs):
            dir = dir.strip('/')
            self.internal_static_dirs[i] = dir
            dir_path = '{}/{}'.format(self.root, dir)
            static_dir = fs.Directory(dir_path, owner=root_dir.owner, group=root_dir.group)
            static_dir.ensure()
