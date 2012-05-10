import os
from fabric.api import env
from quilt.contrib import fs
from quilt.utils import DefaultAttributeDict

env.resources.supervisor.conf_dir = '/etc/supervisor/conf.d'

env.resources.supervisor.program = DefaultAttributeDict({
    'owner': 'root',
    'group': 'root',
    'program_user': 'root',
    'numprocs': 1,
    'priority': 999,
    'autorestart': 'unexpected',
    'startsecs': 1,
    'retries': 3,
    'exitcodes': '0,2',
    'stopsignal': 'TERM',
    'stopwait': 10,
    'stdout_logfile_maxsize': '250MB',
    'stdout_logfile_keep': 10,
    'stderr_logfile_maxsize': '250MB',
    'stderr_logfile_keep': 10,
    'redirect_stderr': 'false',
    'autostart': 'false'
})

class SupervisorConf(fs.File):
    conf_dir = None

    def clean(self):
        if not self.conf_dir:
            self.conf_dir = env.resources.supervisor.conf_dir
        self.path = os.path.join(self.conf_dir, '{}.conf'.format(self.name))
        super(SupervisorConf, self).clean()

    def ensure(self):
        super(SupervisorConf, self).ensure(parents=True)

class Group(SupervisorConf):
    programs = None
    template = 'group.conf'

    def clean(self):
        self.require('programs')
        super(Group, self).clean()

class Program(SupervisorConf):
    command = None
    log_dir = None
    command = None
    environment = None
    program_user = None
    chdir = None
    umask = None
    conf_dir = None
    numprocs = None
    priority = None
    autorestart = None
    startsecs = None
    retries = None
    exitcodes = None
    stopsignal = None
    stopwait = None
    redirect_stderr = None
    stdout_logfile = None,
    stdout_logfile_maxsize = None
    stdout_logfile_keep = None
    stderr_logfile = None
    stderr_logfile_maxsize = None
    strerr_logfile_keep = None
    autostart = None

    template = 'program.conf'

    def clean(self):
        self.require('command')
        super(Program, self).clean()

    def ensure(self):
        super(Program, self).ensure()
        if not self.log_dir:
            self.log_dir = '/var/log/supervisor/{}'.format(self.name)
        fs.Directory(self.log_dir, owner=self.owner, group=self.group).ensure()
