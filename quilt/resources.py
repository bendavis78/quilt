import inspect
from fabric.api import env, abort
from quilt import utils

env.resources = utils.DefaultAttributeDict()
env.dry_run = False
_registry = {}
_remote_import_cache = {}

class Resource(object):
    name = None

    def __init__(self, name, *args, **kwargs):
        module = self.__class__.__module__.split('.')[-2]
        rname = self.__class__.__name__.lower()
        
        caller = None
        # get who defined us by finding the first non-__init__ frame
        for frame in inspect.stack()[1:]:
            if frame[3] == '__init__': 
                continue
            caller = frame
            break

        # Resources with same type/name must be uniquely defined
        key = '{}.{}[{}]'.format(module, rname, name)
        if _registry.get(key):
            self.__dict__ = _registry[key].__dict__
            if (caller[1:2] not in [f[1:2] for f in self._defined_in]): 
                self._defined_in.append(caller)
            # apply kwarg attributes for undefined attributes
            for k,v in kwargs.iteritems():
                if getattr(self, k) is None:
                    setattr(self, k, v)
            return
        
        self._defined_in = [caller]
                    
        _registry[key] = self
        self.key = key
        
        self.module = module
        self.name = name
        self._dummy_exists = False # used for dry_run

        parents = [c for c in self.__class__.mro() if c not in Resource.mro()][1:]
        parents.reverse()

        # Get initial state for first invocation
        state = {}
        for parent in parents:
            parent_module = parent.__module__.split('.')[-2]
            parent_rname = parent.__name__.lower()
            state.update(env.resources[parent_module][parent_rname])
        state.update(env.resources[self.module][rname])
        state.update(env.resources[self.module][rname][name])
        state.update(kwargs)

        for k,v in state.iteritems():
            setattr(self, k, v)
    
    def abort(self, msg):
        from fabric import colors
        help = '\n\n{}, defined in:\n'.format(self.key)
        for frame in self._defined_in:
            help += '  {1}:{2}\n'.format(*frame)
        msg = colors.blue(help) + '\n' + msg
        abort(msg)

    def require(self, *args):
        for arg in args:
            if getattr(self, arg, None) is None:
                msg = '{} is required for resource {}.{}'.format(arg, 
                        self.module, self.__class__.__name__)
                abort(msg)

    def ensure(self):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError

    def exists(self):
        raise NotImplementedError

    def remote_import(self, module):
        from quilt.pushy_support import remote_import
        if not _remote_import_cache.get(module):
            _remote_import_cache[module] = remote_import(module)
        return _remote_import_cache[module]

    def log(self, msg):
        from fabric import colors
        line = ''
        if env.dry_run:
            line += colors.red('[DRY RUN] ')
        line += colors.blue(msg)
        print line

    def clean(self):
        """
        Validates/cleans settings for this resource
        """
        pass
    
    def __repr__(self):
        return self.__class__.__name__


import collections
class ResourceCollection(collections.Iterable):
    def __init__(self, *items):
        self._items = list(items)
        super(ResourceCollection, self).__init__()

    def ensure(self):
        for r in self:
            r.ensure()

    def remove(self):
        for r in self:
            r.remove()

    def clean(self):
        for r in self:
            r.clean()

    def append(self, item):
        self._items.append(item)

    def __iter__(self):
        for r in self._items:
            if isinstance(r, ResourceCollection):
                for sub in r:
                    yield sub
            else:
                yield r

    def __repr__(self):
        return 'ResourceCollection({})'.format(self._items)
