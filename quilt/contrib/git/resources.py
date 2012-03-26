from fabric.api import abort, run, show
from quilt.contrib import fs

class Clone(fs.Directory):
    repo = None

    def ensure(self):
        super(Clone, self).ensure()
        if not self.exists('.git'):
            if self.is_empty():
                cmd = 'git clone {} {}; logout'.format(self.repo, self.path)
                with self.temp_ownership(recursive=True):
                    with show('stdout', 'stderr'):
                        run(cmd)
            else:
                abort('Git directory is not empty and is not a git repository')
