from quilt.resources import Resource
from fabric.api import sudo, hide, settings, env

env.resources.rabbitmq.userpermission.configure = '.*'
env.resources.rabbitmq.userpermission.read = '.*'
env.resources.rabbitmq.userpermission.write = '.*'

class User(Resource):
    password = None
    def ensure(self):
        if not self.exists():
            self.log('Adding rabbitmq user {}'.format(self.name))
            if not env.dry_run:
                sudo('rabbitmqctl add_user {} {}'.format(self.name, self.password))
            else:
                self._dummy_exists = True
        else:
            # ensure password
            self.log('Ensuring password for rabbitmq user {}'.format(self.name))
            if not env.dry_run:
                sudo('rabbitmqctl change_password {} {}'.format(self.name, self.password))
            else:
                self._dummy_exists = True

    def remove(self):
        if not self.exists():
            self.log('Removing rabbitmq user {}'.format(self.name))
            if not env.dry_run:
                sudo('rabbitmqctl delete_user {}'.format(self.name, self.password))

    def exists(self):
        cmd  = "rabbitmqctl list_users | grep '^{}$'".format(self.name)
        with settings(hide('running', 'warnings'), warn_only=True):
            exists = sudo('[ "$({})" ]'.format(cmd))
        return exists.returncode == 0 or self._dummy_exists


class Vhost(Resource):
    def ensure(self):
        if not self.exists():
            self.log('Adding rabbitmq vhost {}'.format(self.name))
            if not env.dry_run:
                sudo('rabbitmqctl add_vhost {}'.format(self.name))
            else:
                self._dummy_exists = True

    def remove(self):
        if not self.exists():
            self.log('Removing rabbitmq vhost {}'.format(self.name))
            if not env.dry_run:
                sudo('rabbitmqctl delete_vhost {}'.format(self.name))

    def exists(self):
        cmd  = "rabbitmqctl list_vhosts | grep '^{}$'".format(self.name)
        with settings(hide('running', 'warnings'), warn_only=True):
            exists = sudo('[ "$({})" ]'.format(cmd))
        return exists.returncode == 0 or self._dummy_exists

class UserPermission(Resource):
    user = None
    vhost = None
    configure = None
    read = None
    write = None

    def ensure(self):
        self.log('Ensuring rabbitmq permissions for {}@{}'.format(self.user, self.vhost))
        if not env.dry_run:
            sudo('rabbitmqctl set_permissions -p {} {} "{}" "{}" "{}"'.format(
                    self.vhost, self.user, self.configure, self.read, self.write))

    def remove(self):
        self.log('Clearing rabbitmq permissions for {}@{}'.format(self.user, self.vhost))
        if not env.dry_run:
            sudo('rabbitmqctl clear_permissions -p {} {}'.format(self.vhost, self.user))

    def exists(self):
        return False
