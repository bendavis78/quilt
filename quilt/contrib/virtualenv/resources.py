from quilt.contrib import fs
from fabric.api import run, env, settings, abort, hide

env.resources.virtualenv.virtualenv.system_site_packages = False

class VirtualEnv(fs.Directory):
    python = None
    system_site_packages = None
    
    def ensure(self):
        parent = fs.Directory(self.path.rsplit('/', 1)[0])
        parent.ensure()
        if self.exists() and self.is_empty():
            self.remove()

        if not self.exists():
            if not self.python:
                self.python = '`which python`'
            
            self.log('Creating virtualenv at {}'.format(self.path))

            # Get virtualenv version
            with hide('stdout'):
                version = run('virtualenv --version')
            version = version.split('.')
            venv_args = ''
            if version < (1,7):
                if not self.system_site_packages:
                    venv_args = ' --no-site-packages'
            else:
                venv_args = ' --{}-site-packages'.format(
                        self.system_site_packages and 'system' or 'no')

            cmd = 'virtualenv{} -p {} {}'.format(venv_args, self.python, self.path)
            if not env.dry_run:
                output_ctrl = settings(hide('stdout'), warn_only=True)
                with output_ctrl, parent.temp_ownership(recursive=True):
                    result = run(cmd)
                if result.return_code != 0:
                    abort('Virtualenv creation failed:\n{}'.format(result))

        super(VirtualEnv, self).ensure()
