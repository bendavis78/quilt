import collections

class DefaultAttributeDict(collections.defaultdict):
    """
    Allows dynamic creation of env values, eg:
    foo.bar.baz = 'qux'
    """
    def __init__(self, *args, **kwargs):
        factory = DefaultAttributeDict
        super(DefaultAttributeDict, self).__init__(factory, *args, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            # to conform with __getattr__ spec
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __repr__(self):
        return dict(self).__repr__()

    def first(self, *names):
        for name in names:
            value = self.get(name)
            if value:
                return value

    def __unicode__(self):
        return "<DefaultAttributeDict>"

