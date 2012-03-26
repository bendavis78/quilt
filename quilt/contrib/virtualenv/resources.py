from quilt.contrib import fs
from fabric.api import run, env, settings, abort, hide

env.resources.virtualenv.virtualenv.no_site_packages = True

class VirtualEnv(fs.Directory):
    python = None
    no_site_packages = None
    
    def ensure(self):
        parent = fs.Directory(self.path.rsplit('/', 1)[0])
        parent.ensure()
        if self.exists() and self.is_empty():
            self.remove()

        if not self.exists():
            if not self.python:
                self.python = '`which python`'
            
            self.log('Creating virtualenv at {}'.format(self.path))
            no_site_pkgs = self.no_site_packages and ' --no-site-packages' or ''
            cmd = 'virtualenv{} -p {} {}'.format(no_site_pkgs, self.python, self.path)
            if not env.dry_run:
                output_ctrl = settings(hide('stdout'), warn_only=True)
                with output_ctrl, parent.temp_ownership(recursive=True):
                    result = run(cmd)
                if result.return_code != 0:
                    abort('Virtualenv creation failed:\n{}'.format(result))

        super(VirtualEnv, self).ensure()
