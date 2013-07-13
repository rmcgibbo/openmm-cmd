import os
import sys

from .IPython.traitlets import Unicode, Instance, List
from .IPython.application import Application
from .IPython.configurable import LoggingConfigurable
from .IPython.text import indent, dedent, wrap_paragraphs
from .IPython.loader import ConfigFileNotFound


class OpenMMApplication(Application):

    """Baseclass for the OpenMM application script, with the methods
    for printing the help text and loading the config file (boring stuff)
    """

    config_file_path = Unicode('openmm_config.py')

    def initialize(self):
        '''Do the first steps to configure the application, including
        finding and loading the configuration file'''
        # load the config file before parsing argv so that
        # the command line options override the config file options
        config = filter(lambda a: a.startswith('--config='), sys.argv)
        if len(config) > 0:
            config_file_path = config[0].split('=')[1]
            self.load_config_file(
                config_file_path, not any(a == 'make_config' for a in sys.argv))
            self.config_file_path = config_file_path
            sys.argv.remove(config[0])

        super(OpenMMApplication, self).initialize()

    def load_config_file(self, path, error_on_not_exists=False):
        try:
            xpath = os.path.abspath(os.path.expanduser(path))
            if not os.path.exists(path) and error_on_not_exists:
                self.error('File does not exist: %s' % path)
            dirname = os.path.dirname(xpath)
            basename = os.path.basename(xpath)
            super(OpenMMBase, self).load_config_file(basename, [dirname])
        except ConfigFileNotFound:
            self.log.warning('No config file was found.')

    def print_description(self):
        "Print the application description"
        lines = []
        lines.append('')
        lines.append(self.short_description)
        lines.append('=' * len(self.short_description))
        lines.append('')
        for l in wrap_paragraphs(self.long_description):
            lines.append(l)
            lines.append('')
        print os.linesep.join(lines)

    def print_subcommands(self):
        """Print the subcommand part of the help."""
        if not self.subcommands:
            return

        lines = ["Subcommands"]
        lines.append('-' * len(lines[0]))
        for subc, (cls, help) in self.subcommands.iteritems():
            lines.append(subc)
            if help:
                lines.append(indent(dedent(help.strip())))
        lines.append('')
        print os.linesep.join(lines)

    def print_options(self):
        if not self.flags and not self.aliases:
            return
        lines = ['Options']
        lines.append('-' * len(lines[0]))
        lines.append('--config=<String>')
        lines.append('    Default: openmm_config.py')
        lines.append(
            '    Path to a configuration file to load from (or to save to, if using `make_config`).')
        print os.linesep.join(lines)
        self.print_flag_help()
        self.print_alias_help()
        print

    def print_help(self, classes=False):
        """Print the help for each Configurable class in self.classes.

        If classes=False (the default), only flags and aliases are printed.
        """
        self.print_subcommands()
        self.print_options()

        if classes:
            # skip self, since it just contains logging information. we put
            # all the configurables into these classes, so that we get nice
            # panels for the user
            for cls in filter(lambda c: c != self.__class__, self.classes):
                cls.class_print_help()
                print
        else:
            print "To see all available configurables, use `--help-all`"
            print

    def error(self, message=None):
        if message:
            self._print_message('%s: error: %s\n'
                    % (os.path.basename(sys.argv[0]), message), sys.stderr)
            self._print_message(
                '\nTo see all available configurables, use `--help-all`\n', sys.stderr)
        sys.exit(2)

    def _print_message(self, message, file=None):
        if message:
            if file is None:
                file = sys.stderr
            file.write(message)

    def flatten_flags(self):
        flags = {}
        aliases = {}

        for cls in filter(lambda c: c != self.__class__, self.classes):
            for name in cls.class_traits().keys():
                aliases[name] = '%s.%s' % (cls.__name__, name)

        return flags, aliases


class AppConfigurable(LoggingConfigurable):

    """Subclass of Configurable that ensure's there arn't any extraneous
    values being set during configuration.
       
    Also adds a validate() method that gets called during initialization
    that you can use to check that things get set correctly.
       
       """
    application = Instance('ipcfg.IPython.application.Application')

    def _application_default(self):
        from .application import Application
        return Application.instance()

    active = List(help='''List of the names of the traits on this Configurable
        that were set during initialization and did not just inherit their
        default value''')

    def __init__(self, config={}):
        for key in config[self.__class__.__name__].keys():
            if key not in self.class_traits():
                self.application.error(
                    '%s has no configurable trait %s' % (self.__class__.__name__, key))

        super(AppConfigurable, self).__init__(config=config)
        self.active = config[self.__class__.__name__].keys()
        self.validate()

    def validate(self):
        "Run any validation on the traits in this class"
        pass

    def config_section(self):
        """Get the config section with all of the activly selected options
        placed in (not commented out as in class_config_section)"""

        def c(s):
            """return a commented, wrapped block."""
            s = '\n\n'.join(wrap_paragraphs(s, 78))

            return '# ' + s.replace('\n', '\n# ')

        # section header
        breaker = '#' + '-' * 78
        s = "# %s configuration" % self.__class__.__name__
        lines = [breaker, s, breaker, '']
        # get the description trait
        desc = self.__class__.class_traits().get('description')
        if desc:
            desc = desc.default_value
        else:
            # no description trait, use __doc__
            desc = getattr(self.__class__, '__doc__', '')
        if desc:
            lines.append(c(desc))
            lines.append('')

        for name, trait in self.__class__.class_traits(config=True).iteritems():
            help = trait.get_metadata('help') or ''
            lines.append(c(help))
            if name in self.active:
                lines.append('c.%s.%s = %r' %
                             (self.__class__.__name__, name, getattr(self, name)))
            else:
                lines.append('# c.%s.%s = %r' %
                             (self.__class__.__name__, name, trait.get_default_value()))
            lines.append('')
        return '\n'.join(lines)

    @classmethod
    def class_get_trait_help(cls, trait, inst=None):
        """Get the help string for a single trait.
        
        If `inst` is given, it's current trait values will be used in place of
        the class default.
        """
        assert inst is None or isinstance(inst, cls)
        lines = []
        header = "--%s=<%s>" % (trait.name, trait.__class__.__name__)
        lines.append(header)
        if inst is not None:
            lines.append(indent('Current: %r' % getattr(inst, trait.name), 4))
        else:
            try:
                dvr = repr(trait.get_default_value())
            except Exception:
                dvr = None  # ignore defaults we can't construct
            if dvr is not None:
                if len(dvr) > 64:
                    dvr = dvr[:61] + '...'
                lines.append(indent('Default: %s' % dvr, 4))
        if 'Enum' in trait.__class__.__name__:
            # include Enum choices
            lines.append(indent('Choices: %r' % (trait.values,)))

        help = trait.get_metadata('help')
        if help is not None:
            help = '\n'.join(wrap_paragraphs(help, 76))
            lines.append(indent(help, 4))
        return '\n'.join(lines)
