from fabric.api import run, hide, settings, env
from quilt.resources import Resource

env.resources.postgresql.user.superuser = False
env.resources.postgresql.user.createdb = False
env.resources.postgresql.user.createrole = False
env.resources.postgresql.privilege.with_grant_option = False

class SqlMixin(object):
    def run_sql(self, sql):
        run('psql template1 -c "{};"'.format(sql))

class Database(Resource):
    owner = None

    def ensure(self):
        if not self.owner:
            self.owner = 'postgres'
        if not self.exists():
            self.log('Creating postgresql database {}'.format(self.name))
            if not env.dry_run:
                run('createdb -O {} {}'.format(self.owner, self.name))
            else:
                self._dummy_exists = True
    
    def remove(self):
        if self.exists():
            self.log('Dropping postgresql database {}'.format(self.name))
            if not env.dry_run:
                run('dropdb {}'.format(self.name))

    def exists(self):
        cmd = "psql template1 -ltA | grep '^{}|'".format(self.name)
        with settings(hide('running','warnings'), warn_only=True):
            exists = run('[ "$({})" ]'.format(cmd))
        return exists.return_code == 0 or self._dummy_exists

class User(SqlMixin, Resource):
    password = None
    superuser = None
    createdb = None
    createrole = None

    def ensure(self):
        if not self.exists():
            self.log('Creating postgresql user {}'.format(self.name))
            cmd = 'createuser --no-superuser --no-createdb --no-createrole {}'.format(self.name)
            if not env.dry_run:
                run(cmd)
            else:
                self._dummy_exists = True
       
        # ensure user attributes, such as password and permissions
        attrs = []
        if self.password:
            attrs.append("UNENCRYPTED PASSWORD '{}'".format(self.password))
        attrs.append(self.superuser and 'SUPERUSER' or 'NOSUPERUSER')
        attrs.append(self.createdb and 'CREATEDB' or 'NOCREATEDB')
        attrs.append(self.createrole and 'CREATEROLE' or 'NOCREATEROLE')
        
        self.log('Ensuring postgresql user attributes for {}'.format(self.name))
        sql = "ALTER USER {} WITH {};".format(self.name, ' '.join(attrs))
        if not env.dry_run:
            self.run_sql(sql)

    def remove(self):
        self.log('Dropping postgresql user {}'.format(self.name))
        if not env.dry_run:
            run('dropuser {}'.format(self.name))

    def exists(self):
        cmd1 = "psql template1 --tuples-only -c 'SELECT rolname FROM pg_catalog.pg_roles'"
        cmd2 = "grep '^ {}$'".format(self.name)
        with settings(hide('running','warnings'), warn_only=True):
            exists = run('[ "$({} | {})" ]'.format(cmd1,cmd2))
        return exists.return_code == 0 or self._dummy_exists

class Privilege(SqlMixin, Resource):
    user = None
    object = None
    with_grant_option = None

    def ensure(self):
        # The simplest way to "ensure" the given privilege is to first revoke, then grant
        self.remove()

        sql = "GRANT {} ON {} TO {}".format(self.name, self.object, self.user)
        if self.with_grant_option:
            sql = "{} WITH GRANT OPTION".format(sql)
        self.log('Granting postgresql privileges for {}'.format(self.user))
        if not env.dry_run:
            self.run_sql(sql)

    def remove(self):
        self.log('Revoking postgresql privileges for {}'.format(self.user))
        sql = "REVOKE {} ON {} FROM {};".format(self.name, self.object, self.user)
        if not env.dry_run:
            self.run_sql(sql)

    def exists(self):
        return False
