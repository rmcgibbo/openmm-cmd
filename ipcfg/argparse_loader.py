from IPython.loader import Config, AliasError
from argparse import ArgumentParser, ArgumentError

class ArgParseLoader(object):
    def __init__(self, argv, classes, aliases):
        parser = ArgumentParser()

        self.config = Config()
        self.argv = argv
        
        all_arguments = {}
        def add_argument(name, *args, **kwargs):
            parser.add_argument(name, *args, **kwargs)
            all_arguments[name] = kwargs['dest']
        
        for cls in classes:
            for name in cls.class_traits(config=True):
                dest = cls.__name__ + '.' + name
                metadata = getattr(cls, name)._metadata
                nargs = metadata.get('nargs', None)

                add_argument('--' + name, type=str, dest=dest, nargs=nargs)

        for k, v in aliases.iteritems():
            try:
                add_argument('--' + k, type=str, dest=v, nargs=None)
            except ArgumentError:
                pass

        known_args, extra_args = parser.parse_known_args(argv)
        self.known_args = known_args
        self.extra_args = extra_args

        if len(extra_args) > 1:
            for item in extra_args[1:]:
                raise AliasError(item[2:], all_arguments)

    def load_config(self):
        for k, v in self.known_args.__dict__.iteritems():
            if v is not None:
                if not isinstance(v, list):
                    v = '"%s"' % v
                exec 'self.config.%s = %s' % (k, v)

        return self.config
