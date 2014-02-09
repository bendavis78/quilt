import os
import stat
import sys
from contextlib import contextmanager
from StringIO import StringIO
from fabric.api import sudo, run, env, put, hide
from quilt.resources import Resource

env.resources.fs.file.owner = 'root'
env.resources.fs.file.group = 'root'
env.resources.fs.file.mode = 0644
env.resources.fs.file.newlines = '\n'
env.resources.fs.directory.mode = 0755
env.resources.fs.directory.no_update = False

class File(Resource):
    path = None
    template = None
    content = None
    owner = None
    group = None
    mode = None
    target = None
    newlines = None
    no_update = None

    directory = False
    symlink = False
    
    def __init__(self, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)
        if not self.path:
            self.path = self.name
        self.__dummy_exists = False
    
    def clean(self):
        self.require('path')

        if not isinstance(self.path, (str, unicode)):
            self.abort('path must be a string (got {})'.format(self.path))

        if not self.path.startswith('/'):
            self.abort('path must be absolute (got "{}")'.format(self.path))

        if self.path.endswith('/'):
            self.directory = True
            self.path = self.path[:-1]

    def ensure(self, parents=False):
        remote_os = self.remote_import('os')
        self.clean()
        parent, name = os.path.split(self.path)

        if parents and parent != '/':
            self.ensure_parents()
        
        if not self.exists():
            if not env.dry_run:
                if self.directory:
                    self.log('Creating directory {} with mode {}'.format(self.path, oct(self.mode)))
                    cmd = 'mkdir -m {} {}'.format(oct(self.mode), self.path)
                    _run = remote_os.access(parent, os.W_OK) and run or sudo
                    _run(cmd)
                elif self.symlink:
                    self.log('Creating symlink {} -> {}'.format(self.target, self.path))
                    cmd = 'ln -s {} {}'.format(self.target, self.path)
                    _run = remote_os.access(parent, os.W_OK) and run or sudo
                    _run(cmd)
                else:
                    self.log('Creating file {} with mode {}'.format(self.path, oct(self.mode)))
                    content = StringIO(self.get_content())
                    use_sudo = not remote_os.access(self.path, os.W_OK)
                    put(content, self.path, use_sudo=use_sudo, mode=self.mode)
            else:
                self._dummy_exists = True
        else:
            # assert correct node type (file/directory/symlink)
            islink = remote_os.path.islink(self.path)
            isdir = remote_os.path.isdir(self.path)
            
            if self.symlink:
                if not islink:
                    self.abort("{} should be symlink but is not".format(self.path))
            elif self.directory:
                if islink or not isdir:
                    self.abort("{} should be a directory but is not".format(self.path))
            elif islink or isdir:
                self.abort("{} should be a regular file, but is not".format(self.path))

        if env.dry_run:
            _dummy_exists = self._dummy_exists
            self._dummy_exists = False
            actually_exists = self.exists()
            self._dummy_exists = _dummy_exists
            if not actually_exists:
                # if this a dry run and the file is being created,
                # there's nothing else we can do
                return 
        
        if self.exists():
            regular_file = not self.directory and not self.symlink
            if regular_file and not self.no_update:
                diff = self.diff()
                if diff:
                    self.log('Updating file {}: \n{}'.format(self.path, diff))
                    if not env.dry_run:
                        content = StringIO(self.get_content())
                        use_sudo = not remote_os.access(self.path, os.W_OK)
                        put(content, self.path, use_sudo=use_sudo, mode=self.mode)

            # check ownership
            current_stat = remote_os.stat(self.path)
            current_uid = current_stat.st_uid
            current_gid = current_stat.st_gid
            uid = self.get_uid(self.owner)
            gid = self.get_gid(self.group)
            if current_uid != uid or current_gid != gid:
                self.chown(self.owner, self.group)

            # check file mode
            current_mode = stat.S_IMODE(current_stat.st_mode)
            # if our required mode does not specify setuid/setgid, then we don't
            # care if the resource has it.
            if not self.mode & stat.S_ISUID and current_mode & stat.S_ISUID:
                current_mode = current_mode ^ stat.S_ISUID
            if not self.mode & stat.S_ISGID and current_mode & stat.S_ISGID:
                current_mode = current_mode ^ stat.S_ISGID
            if oct(current_mode) != oct(self.mode):
                self.chmod(self.mode)

    def ensure_parents(self):
        parent, name = os.path.split(self.path)
        Directory(parent).ensure(parents=True)
    
    def chmod(self, mode):
        remote_os = self.remote_import('os')
        current_stat = remote_os.stat(self.path)
        current_mode = stat.S_IMODE(remote_os.stat(self.path).st_mode)

        self.log('Changing permissions on {} from {} to {}'.format(self.path,
                oct(current_mode), oct(self.mode)))

        if env.dry_run:
            return

        cmd = 'chmod {} {}'.format(oct(self.mode), self.path)

        # See if we have write permissions on this path
        if current_stat.st_uid == remote_os.getuid():
            run(cmd)
        else:
            sudo(cmd)

    def chown(self, owner, group=None, recursive=False):
        remote_os = self.remote_import('os')
        current_stat = remote_os.stat(self.path)
        chown_str = group and '{}:{}'.format(owner, group) or owner

        self.log('Setting {}ownership to {} on {}'.format( 
                (recursive and 'recursive ' or ''), chown_str, self.path))
        
        owner_changed = self.get_uid(owner) != current_stat.st_uid

        if env.dry_run:
            return

        if owner_changed:
            sudo('chown {}{} {}'.format((recursive and '--recursive ' or ''),
                    chown_str, self.path))
        elif group:
            cmd = 'chgrp {} {}'.format(group, self.path)
            if current_stat.st_uid == remote_os.getuid():
                run(cmd)
            else:
                sudo(cmd)

    def get_uid(self, user):
        if type(user) == int:
            return user
        if not isinstance(user, basestring):
            self.abort('Invalid user name: {}'.format(user))
        pwd = self.remote_import('pwd')
        try:
            return pwd.getpwnam(user)[2]
        except KeyError:
            self.abort('User "{}" not found'.format(user))

    def get_gid(self, group):
        if type(group) == int:
            return group
        if not isinstance(group, basestring):
            self.abort('Invalid group name: {}'.format(group))
        grp = self.remote_import('grp')
        try:
            return grp.getgrnam(group)[2]
        except KeyError:
            self.abort('Group "{}" not found'.format(group))
 

    def get_content(self):
        if self.content is not None:
            return self.content

        if self.template:
            return self.render_template()

        return ''

    def render_template(self):
        import jinja2
        tpl_path = self.get_template_path(self.template)
        tplenv = jinja2.Environment(loader=jinja2.FileSystemLoader(tpl_path))
        try:
            template = tplenv.get_template(self.template)
            return template.render(**self.__dict__)
        except jinja2.exceptions.TemplateSyntaxError, e:
            self.abort('Template syntax error in {}: {}'.format(self.template, e))

    def get_template_path(self, name):
        module = sys.modules[self.__class__.__module__].__file__
        return os.path.join(os.path.dirname(module), 'templates')

    def exists(self, subpath=None):
        remote_os = self.remote_import('os')
        path = self.path
        if subpath:
            path = os.path.join(path, subpath)
        return remote_os.path.exists(path) or self._dummy_exists

    def remove(self):
        assert False
        remote_os = self.remote_import('os')
        self.log('Removing {}'.format(self.path))
        if env.dry_run:
            return
        _run = remote_os.access(self.path, os.W_OK) and run or sudo
        if self.directory:
            _run('rmdir {}'.format(self.path))
        else:
            _run = remote_os.access(self.path, os.W_OK) and run or sudo
            _run('rm {}'.format(self.path))

    def fmode_to_dirmode(self, mode):
        "Returns directory-equivelant of file mode. Basically sets executible for every readable u/g/o part."
        if mode & stat.S_IRUSR:
            mode = mode | stat.S_IXUSR
        if mode & stat.S_IRGRP:
            mode = mode | stat.S_IXGRP
        if mode & stat.S_IROTH:
            mode = mode | stat.S_IXOTH
        return mode

    def diff(self):
        from difflib import unified_diff
        remote_os = self.remote_import('os')
        # Get remote file's contents
        _run = remote_os.access(self.path, os.R_OK) and run or sudo
        with hide('running', 'stdout'):
            current_content = _run('cat {}'.format(self.path))
        old = self.normalize_newlines(current_content).splitlines(True)
        new = self.normalize_newlines(self.get_content()).splitlines(True)
        diff = unified_diff(old, new, fromfile='old', tofile='new')
        return ''.join([l for l in diff])

    def normalize_newlines(self, content):
        lines = content.splitlines()
        return self.newlines.join(lines)
    
    @contextmanager
    def temp_ownership(self, access=os.W_OK, recursive=False, force=False):
        """
        Context manager which temporarily changes owner of this path if needed.

        Some commands require write access to paths for which the currently 
        logged in user does not have access.  If, for example, such a command 
        is unsafe to run using sudo (such as git clone), this context manager 
        can be used.
        """
        remote_os = self.remote_import('os')
        if force or not remote_os.access(self.path, access):
            if not force:
                self.log('Current user does not have write access to {}, temporarily changing owners...'.format(self.path))
            self.chown(env.user, recursive=recursive)
            yield True # we needed to chown
            self.chown(self.owner, recursive=recursive)
        else:
            yield False # we didn't need to chown


class Directory(File): 
    directory = True

    def is_empty(self):
        if not self.exists():
            return True
        remote_os = self.remote_import('os')
        return remote_os.listdir(self.path) == []

    def recursive_chmod(self, chmod_arg, use_sudo=False):
        cmd = 'chmod --recursive {} {}'.format(chmod_arg, use_sudo)
        if sudo:
            sudo(cmd)
        else:
            run(cmd)

class Symlink(File):
    symlink = True

    def clean(self):
        super(Symlink, self).clean()
        self.require('target')
