#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys
from simtk import unit

# command line configuration system
from ipcfg.extratraitlets import Quantity
from ipcfg.openmmapplication import OpenMMApplication, AppConfigurable
from ipcfg.IPython.traitlets import (Int, Bool, Bytes, CaselessStrEnum,
                                     Instance, Enum, Float, TraitError)
from ipcfg.IPython.application import Application

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class General(AppConfigurable):

    """General options for the application.
    """

    forcefield = CaselessStrEnum(['amber96', 'amber99sb', 'amber99sb-ildn',
        'amber99sb-nmr', 'amber03', 'amber10'], allow_none=False, config=True,
        default_value='amber99sb-ildn', help=''' Forcefield to use for the
        protein atoms. For details, consult the literature.''')
    water = CaselessStrEnum(['SPC/E', 'TIP3P', 'TIP4-Ew', 'TIP5P', 'Implict'],
        config=True, default_value='TIP3P', allow_none=True, help='''Forcefield
        to use for water in the simulation.''')
    platform = CaselessStrEnum(['Reference', 'OpenCL', 'CUDA'],
        allow_none=True, help='''OpenMM runs simulations on three platforms:
        Reference, CUDA, and OpenCL. If not specified, the fastest available
        platform will be selected automatically.''', config=True)
    precision = CaselessStrEnum(['Single', 'Mixed', 'Double'], config=True,
        defaut_value='Mixed', help='''Level of numeric precision to use for
        calculations.''')
    coords = Bytes(config=True, help='''OpenMM can take a pdb...''')
    #pdb_file = Instance(app.PDBFile)

    def validate(self):
        if 'precision' in self.specified_config_traits and self.precision != 'Double' and self.platform == 'Reference':
            raise TraitError('Manually setting the precision is only '
                             'appropriate on the OpenCL and CUDA platforms')

    def load_coords(self):
        "Load coordinate/topology files from disk"
        if self.coords.endswith('.pdb'):
            if self.pdb_file is None:
                script("pdb = app.PDBFile('%s')" % self.coords)
                self.pdb_file = app.PDBFile(self.coords)
        else:
            raise RuntimeError()

    def get_forcefield(self):
        "Create the forcefield object"
        files = [self.forcefield.replace('-', '').lower() + '.xml']
        if self.water in ['SPC/E', 'TIP3P', 'TIP4-Ew', 'TIP5P']:
            files.append(
                self.water.replace('/', '').replace('-', '').lower() + '.xml')
        elif self.water == 'Implicit':
            if self.forcefield == 'amber96':
                files.append('amber96_obc.xml')
            elif self.forcefield.startswith('amber99'):
                files.append('amber99_obc.xml')
            elif self.forcefield == 'amber03':
                files.append('amber03_obc.xml')
            elif self.forcefield == 'amber10':
                files.append('amber10_obc.xml')
            else:
                raise RuntimeError()

        script('forcefield = app.ForceField(%s)' %
               ', '.join(["'%s'" % f for f in files]))
        return app.ForceField(*files)

    def get_positions(self):
        "Get the positions for every atom"

        self.load_coords()
        if self.pdb_file is not None:
            script('positions = pdb.positions')
            return self.pdb_file.positions
        raise RuntimeError()

    def get_topology(self):
        "Get the system topology"

        self.load_coords()
        if self.pdb_file is not None:
            script('topology = pdb.topology')
            return self.pdb_file.topology
        raise RuntimeError()

    def get_platform(self):
        "Get the platform"

        if self.platform is None:
            script('platform = None')
            return None
        else:
            script("platform = mm.Platform.getPlatformByName('%s')" %
                   self.platform)
            return mm.Platform.getPlatformByName(self.platform)

    def get_platform_properties(self):
        "Get any specified platorm properties"

        if self.platform is None or self.platform == 'Reference':
            pp = None
        elif self.platform == 'CUDA':
            pp = {'CudaPrecision': self.precision.lower()}
        elif self.platform == 'OpenCL':
            pp = {'OpenCLPrecision': self.precision.lower()}
        else:
            raise RuntimeError()

        script('platformProperties = %s' % pp)
        return pp


class System(AppConfigurable):

    "Parameters for the system"

    nb_method = CaselessStrEnum(['NoCutoff', 'CutoffNonPeriodic',
        'CutoffPeriodic', 'Ewald', 'PME'], config=True, default_value='PME',
        allow_none=False, help='''Method for calculating long range
        non-bondend interactions. Refer to the user guide for a detailed
        discussion.''')
    ewald_tol = Float(0.0005, config=True, allow_none=False, help='''The error
        tolerance is roughly equal to the fractional error in the forces due
        to truncating the Ewald summation.''')
    constraints = CaselessStrEnum(['None', 'HBonds', 'AllBonds', 'HAngles'],
        default_value='HBonds', allow_none=False, config=True, help='''Applying
        constraints to some of the atoms can enable you to take longer
        timesteps.''')
    rigid_water = Bool(True, config=True, help='''Keep water rigid. Be aware
        that flexible water may require you to further reduce the integration
        step size, typically to about 0.5 fs.''')
    cutoff = Quantity(1.0 * unit.nanometers, config=True,
        help='''Cutoff for long-range non-bonded interactions. This option is
        usef for all non-bonded methods except for "NoCutoff".''')
    rand_vels = Bool(True, config=True, help='''Initialize the system
        with random initial velocities, drawn from the Maxwell Boltzmann
        distribution.''')
    gen_temp = Quantity(300 * unit.kelvin, config=True, help='''Temperature
        used for generating initial velocities. This option is only used if
        rand_vels == True.''')

    def active_config_traits(self):
        """Construct a list of all of the configurable traits that are currently
        'active', in the sense that their value will have some effect on the
        simulation.
        """
        active_traits = ['nb_method', 'constraints', 'rigid_water', 'rand_vels']
        if self.nb_method in ['PME', 'Ewald']:
            active_traits.append('ewald_tol')
        if self.rand_vels:
            active_traits.append('gen_temp')
        return active_traits

    def validate(self):
        """Run some validation checks.
        """
        # note that many of these checks are sort of redundant with the computation
        # of the active traits, but they provide a nicer english explanation of
        # what's wrong with the configuration, which is important for the user.
        if self.nb_method not in ['PME', 'Ewald'] and 'ewald_tol' in self.specified_config_traits:
            raise TraitError("The Ewald summation tolerance option, 'ewald_tol', "
                             "is only appropriate to set when 'nb_method' is "
                             "PME or Ewald.")
        if not self.rand_vels and 'gen_temp' in self.specified_config_traits:
            raise TraitError("The generation temperature option, 'gen_temp' "
                             "is only appropriate when 'rand_vels' is True")

class Dynamics(AppConfigurable):

    "Parameters for the integrator, thermostats and barostats"

    integrator = CaselessStrEnum(['Langevin', 'Verlet', 'Brownian',
        'VariableLangevin', 'VariableVerlet'], config=True, allow_none=False,
        default_value='Langevin', help='''OpenMM offers a choice of several
        different integration methods. Refer to the user guide for
        details.''')
    tolerance = Float(0.0001, config=True, help='''Tolerance for variable
        timestep integrators ('VariableLangevin', 'VariableVerlet'). Smaller
        values will produce a smaller average step size.''')
    collision_rate = Quantity(1.0 / unit.picoseconds, config=True,
        help='''Friction coefficient, for use with stochastic integrators or
        the Anderson thermostat.''')
    temp = Quantity(300 * unit.kelvin, config=True, help='''Temperature
        of the heat bath, used either by a stochastic integrator or the
        Andersen thermostat to maintain a constant temperature ensemble.''')
    barostat = CaselessStrEnum(['MonteCarlo', 'None'], allow_none=False,
        config=True, default_value='None', help='''Activate a barostat for
        pressure coupling. The MC barostat requires temperature control
        (stochastic integrator or Andersen thermostat) to be in effect
        as well.''')
    pressure = Quantity(1 * unit.atmosphere, config=True, help='''Pressure
        target, used by a barostat.''')
    barostat_interval = Int(25, config=True, help='''The frequency (in time
        steps) at which Monte Carlo pressure changes should be attempted.
        This option is only invoked when barostat == MonteCarlo.''')
    thermostat = CaselessStrEnum(['Andersen', 'None'], allow_none=False,
        config=True, default_value='None', help='''Activate a thermostat to
        maintain a constant temperature simulation.''')
    dt = Quantity(2 * unit.femtoseconds, config=True, help='''Timestep
        for fixed-timestep integrators.''')

    def active_config_traits(self):
        """Construct a list of all of the configurable traits that are currently
        'active', in the sense that their value will have some effect on the
        simulation.
        """
        active_traits = ['integrator', 'barostat', 'thermostat']
        if self.integrator in ['Langevin', 'Verlet', 'Brownian']:
            active_traits.append('dt')
        else:
            active_traits.append('tolerance')

        if self.barostat == 'MonteCarlo':
            active_traits.append('pressure')
            active_traits.append('barostat_interval')

        if self.integrator in ['Langevin', 'VariableLangevin', 'Brownian'] or self.thermostat == 'Andersen':
            active_traits.append('temp')
        return active_traits

    def validate(self):
        """Run some validation checks.
        """
        # note that many of these checks are sort of redundant with the computation
        # of the active traits, but they provide a nicer english explanation of
        # what's wrong with the configuration, which is important for the user.

        thermostatted = (self.integrator in ['Langevin', 'Brownian', 'VariableLangevin'] or
                         self.thermostat == 'Andersen')

        if 'tolerance' in self.specified_config_traits and self.integrator not in ['VariableLangevin', 'VariableVerlet']:
            raise TraitError("The variable integrator error threshold option, 'tolerance',"
                             "is only appropriate when using the VariableLangevin or "
                             "VariableVerlet integrators.")
        if 'dt' in self.specified_config_traits and self.integrator not in ['Langevin', 'Verlet', 'Brownian']:
            raise TraitError("The timestep option, 'dt', is only appropriate when using "
                             "a fixed timestep integrator.")

        if 'collision_rate' in self.specified_config_traits and not thermostatted:
            raise TraitError("The friction coefficient option, 'collision_rate', is only "
                             "appropriate when using a stochastic integrator (e.g. Langevin, "
                             "Brownian, VariableLangevin) or an Andersen thermostat.")
        if 'temp' in self.specified_config_traits and not thermostatted:
            raise TraitError("The temperature target option, 'temp', is only "
                             "appropriate when using a thermostat or stochastic integrator.")

        if 'pressure' in self.specified_config_traits and not self.barostat == 'MonteCarlo':
            raise TraitError("The pressure target option, 'pressure', is only "
                             "appropriate when using the Monte Carlo barostat")
        if 'barostat_interval' in self.specified_config_traits and not self.barostat == 'MonteCarlo':
            raise TraitError("The barostat interval option, 'barostat_interval', is only "
                             "appropriate when using the Monte Carlo barostat.")

        if (self.barostat == 'MonteCarlo') and not thermostatted:
            raise TraitError("You should only use the MonteCarlo barostat on a system that is "
                             "under temperature control.")

    def get_integrator(self):
        "Fetch the integrator"

        if self.integrator == 'Langevin':
            script('integrator = mm.LangevinIntegrator(%s, %s, %s)'
                   % (self.temp, self.collision_rate, self.dt))
            return mm.LangevinIntegrator(self.temp, self.collision_rate, self.dt)
        elif self.integrator == 'Brownian':
            script('integrator = mm.BrownianIntegrator(%s, %s, %s)'
                   % (self.temp, self.collision_rate, self.dt))
            return mm.BrownianIntegrator(self.temp, self.collision_rate, self.dt)
        elif self.integrator == 'Verlet':
            script('integrator = mm.VerletIntegrator(%s)' % self.dt)
            return mm.VerletIntegrator(self.dt)
        elif self.integrator == 'VariableVerlet':
            script('integrator = mm.VariableVerletIntegrator(%s)' %
                   self.tolerance)
            return VariableVerletIntegrator(self.tolerance)
        elif self.integrator == 'VariableLangevin':
            script('integrator = mm.VariableLangevinIntegrator(%s)' %
                   self.tolerance)
            return VariableLangevinIntegrator(self.tolerance)
        else:
            raise RuntimeError()

    def get_forces(self):
        "Get additional OpenMM force objects to be added to the system"

        forces = []
        if self.barostat == 'MonteCarlo':
            script('system.addForce(mm.MonteCarloBarostat(%s, %s, %s)' %
                  (self.pressure, self.temp, self.barostat_interval))
            forces.append(mm.MonteCarloBarostat(self.pressure, self.temp,
                                                self.barostat_interval))
        if self.thermostat == 'Andersen':
            script('system.addForce(mm.AndersenThermostat(%s, %s)' %
                  (self.temp, self.collision_rate))
            forces.append(
                mm.AndersenThermostat(self.temp, self.collision_rate))

        return forces


class Simulation(AppConfigurable):

    "Parameters for the simulation object, including reporters, number of steps, etc"

    n_steps = Int(1000, config=True,
                  help='''Number of steps of simulation to run.''')
    minimize = Bool(True, config=True, help='''First perform local energy
        minimization, to find a local potential energy minimum near the
        starting structure.''')
    traj_file = Bytes('output.dcd', config=True, help='''Filename to save the
        resulting trajectory to, in DCD format.''')
    traj_freq = Int(1000, config=True, help='''Frequency, in steps, to
        save the state to disk in the DCD format.''')
    statedata_freq = Int(1000, config=True, help='''Frequency, in steps,
        to print summary statistics on the state of the simulation.''')

    def validate(self):
        pass


class MakeConfig(Application):

    "Subapplication that creates and saves a config file"

    def start(self, config_file_path):

        # all lines of the new config file
        lines = ['# Configuration file for openmm.']
        lines.append('')
        lines.append('from simtk.unit import *')
        lines.append('c = get_config()')
        lines.append('')

        for cls in filter(lambda c: c != OpenMM, OpenMM.classes):
            lines.append(cls.class_config_section())

        if os.path.exists(config_file_path):
            self.log.error("%s already exists. I don't want to overwrite it, "
                           "so I'm backing off...", config_file_path)
            sys.exit(1)

        print('Saving new template config file to %s' % config_file_path)

        with open(config_file_path, 'w') as f:
            f.write(os.linesep.join(lines))


class OpenMM(OpenMMApplication):
    short_description = 'OpenMM: GPU Accelerated Molecular Dynamics'
    long_description = '''Run a molecular simulaton using the OpenMM toolkit.'''

    # Configured Classes. During initialization, these guys are
    # instantiated based on the config file / command line.
    classes = [General, System, Dynamics, Simulation]
    general = Instance(General)
    system = Instance(System)
    dynamics = Instance(Dynamics)
    simulation = Instance(Simulation)

    subcommands = {'make_config': (MakeConfig,
                                   '''Make a template input configuration file''')}

    log_level = Enum(
        (0, 10, 20, 30, 40, 50, 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'),
        default_value='INFO', config=True, help="""Set the log level by
         value or name.""")

    def validate(self):
        super(OpenMM, self).validate()
        if self.dynamics.integrator in ['Langevin', 'Verlet']:
            if self.system.constraints == 'None' and self.dynamics.dt > 1*unit.femtoseconds:
                raise TraitError('You are likely using too large a timestep. With the '
                                 'Langevin or Verlet integrators, without constraints a '
                                 'timestep over 1 femtosecond is not recommended.')
            if self.system.constraints in ['HBonds', 'AllBonds'] and self.dynamics.dt > 2*unit.femtoseconds:
                raise TraitError('You are likely using too large a timestep. With the '
                                 'Langevin or Verlet integrators and bond constraints, a '
                                 'timestep over 2 femtoseconds is not recommended.')
            if self.system.constraints == 'HAngles' and self.dynamics.dt > 4*unit.femtoseconds:
                raise TraitError('You are likely using too large a timestep. With the '
                                 'Langevin or Verlet integrators and HAngle constraints, a '
                                 'timestep over 4 femtoseconds is not recommended.')

        if ((self.general.platform != 'Reference') and
            (self.general.precision in ['Single', 'Mixed'])  and
            (self.system.nb_method == 'PME') and (self.ewald_tol < 5e-5)):
            raise TraitError('Your ewald error tolerance is so low that is numerical '
                             'error is likely to cause the forces to become less accurate, '
                             'not more. Very small error tolerances only work in double '
                             'precision. (This only applies to PME. Ewald has no problem '
                             'with them.')
        if (self.general.water == 'Implicit') and  (self.system.nb_method in ['CutoffPeriodic', 'Ewald', 'PME']):
            raise TraitError('Using periodic boundary conditions with implict solvent? '
                             'That\'s a very strange choice.  You don\'t really want '
                             'periodic boundary conditions with implicit solvent, do you?')
        if (self.dynamics.barostat != 'None') and  (self.system.nb_method in  ['NoCutoff', 'CutoffNonPeriodic']):
            raise TraitError("It doesn't make sense to use a barostat with no cutoffs, "
                             "since %s implies you're using a nonperiodic system. But adjusting "
                             "the box volume (the way that the barostat controls the pressure) "
                             "will have no effect." % self.system.nb_method)

    def start(self):
        if self.subapp is not None:
            return self.subapp.start(self.config_file_path)


        print 'starting!'

        print 'Active Options'
        print self.general.active_config_traits()
        print self.system.active_config_traits()
        print self.dynamics.active_config_traits()
        print self.simulation.active_config_traits()

        print '\nSpecified Options'
        print self.general.specified_config_traits
        print self.system.specified_config_traits
        print self.dynamics.specified_config_traits
        print self.simulation.specified_config_traits
        #import IPython as ip
        #ip.embed()


    def initialize(self, argv=None):
        super(OpenMM, self).initialize(argv)
        try:
            self.initialize_configured_classes()
            self.validate()
        except TraitError as e:
            self.error(e)


if __name__ == '__main__':
    OpenMM.launch_instance()
