from .IPython.loader import Config, AliasError
from .IPython.traitlets import Bool
from optparse import OptionParser

class OptParseLoader(object):
    def __init__(self, argv, classes, aliases):
        parser = OptionParser()

        self.config = Config()
        self.argv = argv
        
        all_options = {}
        def add_option(name, *args, **kwargs):
            parser.add_option(name, *args, **kwargs)
            all_options[name] = kwargs['dest']
        
        for cls in classes:
            for name in cls.class_traits(config=True):
                dest = cls.__name__ + '.' + name
                trait = getattr(cls, name)
                nargs = trait._metadata.get('nargs', None)
                action = trait._metadata.get('action', None)
                if action == 'append':
                    add_option('--' + name, type=str, dest=dest, nargs=nargs, action='append')
                else:
                    add_option('--' + name, type=str, dest=dest, nargs=nargs)

        for k, v in aliases.iteritems():
            try:
                add_option('--' + k, type=str, dest=v, nargs=None)
            # except ArgumentError:
            except: # Not sure how optparse handles these.
                pass

        known_args, extra_args = parser.parse_args(argv)
        self.known_args = known_args
        self.extra_args = extra_args

        if len(extra_args) > 1:
            for item in extra_args[1:]:
                raise AliasError(item[2:], all_options)

    def load_config(self):
        for k, v in self.known_args.__dict__.iteritems():
            if v is not None:
                if isinstance(v, basestring):
                    v = '"%s"' % v
                elif isinstance(v, list):
                    pass
                exec 'self.config.%s = %s' % (k, v)

        return self.config
