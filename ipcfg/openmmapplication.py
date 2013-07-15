#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


import os
import sys
import copy


from .IPython import traitlets
from .IPython.traitlets import Bytes, Instance, List, TraitError, Unicode
from .IPython.application import Application
from .IPython.configurable import LoggingConfigurable
from .IPython.text import indent, dedent, wrap_paragraphs
from .IPython.loader import ConfigFileNotFound

#-----------------------------------------------------------------------------
# Dirty Hacks
#-----------------------------------------------------------------------------

# Replace the function add_article in traitlets with a version that makes
# the error message thrown when a trait is invalid better.

# WITH HACK
# $ openmm --dt=1.0*A
# openmm: error: The 'dt' trait of the dynamics section must have units of
# femtosecond, but a value in units of angstrom was specified.

# WITHOUT HACK
# $ openmm --dt=1.0*A
# openmm: error: The 'dt' trait of a Dynamics must have units of femtosecond,
# but a value in units of angstrom was specified.

_super_traitlets_add_article = traitlets.add_article
def _traitlets_add_article(name):
    if name in [c.__name__ for c in AppConfigurable.__subclasses__()]:
        return 'the %s section' % name.lower()
    else:
        return _super_traitlets_add_article(object)
traitlets.add_article = _traitlets_add_article


#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class OpenMMApplication(Application):

    """Baseclass for the OpenMM application script, with the methods
    for printing the help text and loading the config file (boring stuff)
    """
    configured_classes = List()
    option_description = Unicode('')

    def initialize(self, argv=None):
        '''Do the first steps to configure the application, including
        finding and loading the configuration file'''
        # load the config file before parsing argv so that
        # the command line options override the config file options
        if argv is None:
            argv = copy.copy(sys.argv)
        config_flags = filter(lambda a: a.startswith('--config='), argv)
        if len(config_flags) > 0:
            self.config_file_path = config_flags[0].split('=')[1]
            argv = [a for a in argv if a != config_flags[0]]

        # if the user was using make_config or did not specify a path
        # to the config file, then don't error if no config file is found.
        error_on_no_config_file = not (any(a == 'make_config' for a in sys.argv) or len(config_flags) == 0)
        self.load_config_file(self.config_file_path, error_on_no_config_file)

        super(OpenMMApplication, self).initialize(argv)


    def initialize_configured_classes(self):
        for klass in filter(lambda c: c != self.__class__, self.classes):
            traitname = klass.__name__.lower()
            self.log.debug('Initializing %s options from config/command line.' % traitname)
            trait = self.class_traits()[traitname]
            if trait is None:
                raise AttributeError(
                    '''To use initialize_classes, you need to make Instance trait on your application
                    with the name of each of the items in classes that will be used to
                    hold the initialized value. I coulndn't find an Instance trait named
                    %s''' % traitname)

            if not isinstance(trait, Instance):
                raise AttributeError("%s needs to be an Instance trait" % trait)

            instantiated = klass(config=self.config)
            self.configured_classes.append(instantiated)
            setattr(self, traitname, instantiated)

    def validate(self):
        for cls in self.configured_classes:
            cls.validate()

    def load_config_file(self, path, error_on_not_exists=False):
        try:
            xpath = os.path.abspath(os.path.expanduser(path))
            if not os.path.exists(path) and error_on_not_exists:
                self.error('File does not exist: %s' % path)
            dirname = os.path.dirname(xpath)
            basename = os.path.basename(xpath)
            super(OpenMMApplication, self).load_config_file(basename, [dirname])
            self.log.info('Config file was found!')
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
            self.log.error(str(message))
            self._print_message(
                '\nTo see all available configurables, use `--help-all`\n', sys.stderr)
        sys.exit(2)

    def _print_message(self, message, file=None):
        if message:
            if file is None:
                file = sys.stderr
            file.write(message)

    def flatten_flags(self):
        """Hook back into the superclass to enable command line options to be
        parsed like aliases even when they're not printed out in the alias
        table.

        If there's an option like --ConfigurableClass.option, this little
        hack makes it possible to specify it using --option.

        This method is called in the superclass when parsing the command
        line options, so we just hijack it to spoof the alias table. Maybe
        there is better way to do this?
        """
        flags, aliases = super(OpenMMApplication, self).flatten_flags()
        for cls in filter(lambda c: c != self.__class__, self.classes):
            for name in cls.class_traits(config=True).keys():
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
        from .IPython.application import Application
        return Application.instance()

    specified_config_traits = List(help='''List of the names of the traits on this
        Configurable that were set during initialization and did not just
        inherit their default value. (Which traits were actually set in the
        command line or config file).''')

    def active_config_traits(self):
        return self.class_traits(config=True).keys()


    def __init__(self, config={}):
        for key in config[self.__class__.__name__].keys():
            if key not in self.class_traits():
                self.application.error(
                    '%s has no configurable trait %s' % (self.__class__.__name__, key))

        super(AppConfigurable, self).__init__(config=config)
        self.specified_config_traits = config[self.__class__.__name__].keys()

    def validate(self):
        "Run any validation on the traits in this class"
        pass

    def config_section(self):
        """Get the config section with all of the activly selected options
        placed in (not commented out as in cls.class_config_section)"""

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

        active_config_traits = self.active_config_traits()

        for name, trait in self.__class__.class_traits(config=True).iteritems():
            help = trait.get_metadata('help') or ''
            lines.append(c(help))
            if name in active_config_traits:
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
