IPython-based Configuration System
==================================

OpenMM command line app config file framework / parser based on IPython traitlets
system.

Features
--------

1. Units
  ```
  $ openmm --dt=1
  [OpenMM] WARNING | No config file was found.
  [OpenMM] ERROR | The 'dt' trait of the dynamics section must have units of
  femtosecond, but a value without units, 1, was specified. To specify units,
  use a syntax like --dt=2*femtosecond on the command line, or c.Dynamics.dt =
  2*femtosecond in the config file.
  ```

2. Did you mean?
  ```
  $ openmm --collision_ratee=1/picoseconds
  [OpenMM] WARNING | No config file was found.
  [OpenMM] ERROR | Unrecognized option: 'collision_ratee'. Did you mean
  'collision_rate'?
  ```

3. Ensuring that supplied configuration options actually make sense
  ```
  $ openmm --temp=300*kelvin --integrator=Verlet --thermostat=None
  [OpenMM] WARNING | No config file was found.
  [OpenMM] ERROR | The temperature target option, 'temp', is only appropriate when
  using a thermostat or stochastic integrator.

  $ openmm --barostat=None --pressure=1*atmosphere
  [OpenMM] WARNING | No config file was found.
  [OpenMM] ERROR | The pressure target option, 'pressure', is only appropriate
  when using the Monte Carlo barostat.
  ```

4. Config File
  
  After running a simulation, all of the configuration options you specified --
  either in your input config file or on the command line -- are printed to
  a runnable output config file.
  
  Config options that were actually in effect during your simulation are written
  there, and config options that were not in effect, e.g. the `barostat_interval`
  option if you'd if you were using `barostat=None`, are commented out in the
  file.
    
  ```
  $ cat config.out.py
  # Configuration file for openmm
  # Generated 2013-07-14 19:13:43.543040
  # Command line: /Library/Frameworks/EPD64.framework/Versions/7.3/bin/openmm --integrator=VariableVerlet
  # OpenMM version UNKNOWN.UNKNOWN

  from simtk.unit import *
  c = get_config()

  #------------------------------------------------------------------------------
  # General configuration
  #------------------------------------------------------------------------------

  # General options for the application.

  # Forcefield to use for water in the simulation.
  c.General.water = 'TIP3P'

  # OpenMM runs simulations on three platforms: Reference, CUDA, and OpenCL. If
  # not specified, the fastest available platform will be selected automatically.
  c.General.platform = None

  # OpenMM can take a pdb...
  c.General.coords = ''

  # Level of numeric precision to use for calculations.
  c.General.precision = None

  # Forcefield to use for the protein atoms. For details, consult the literature.
  c.General.forcefield = 'amber99sb-ildn'

  #------------------------------------------------------------------------------
  # System configuration
  #------------------------------------------------------------------------------

  # Parameters for the system

  # Cutoff for long-range non-bonded interactions. This option is usef for all
  # non-bonded methods except for "NoCutoff".
  # c.System.cutoff = 1.0*nanometer

  # Initialize the system with random initial velocities, drawn from the Maxwell
  # Boltzmann distribution.
  c.System.rand_vels = True

  # The error tolerance is roughly equal to the fractional error in the forces due
  # to truncating the Ewald summation.
  c.System.ewald_tol = 0.0005

  # Keep water rigid. Be aware that flexible water may require you to further
  # reduce the integration step size, typically to about 0.5 fs.
  c.System.rigid_water = True

  # Temperature used for generating initial velocities. This option is only used
  # if rand_vels == True.
  c.System.gen_temp = 300*kelvin

  # Method for calculating long range non-bondend interactions. Refer to the user
  # guide for a detailed discussion.
  c.System.nb_method = 'PME'

  # Applying constraints to some of the atoms can enable you to take longer
  # timesteps.
  c.System.constraints = 'HBonds'

  #------------------------------------------------------------------------------
  # Dynamics configuration
  #------------------------------------------------------------------------------

  # Parameters for the integrator, thermostats and barostats

  # Friction coefficient, for use with stochastic integrators or the Anderson
  # thermostat.
  # c.Dynamics.collision_rate = 1.0/picosecond

  # Activate a barostat for pressure coupling. The MC barostat requires
  # temperature control (stochastic integrator or Andersen thermostat) to be in
  # effect as well.
  c.Dynamics.barostat = 'None'

  # Activate a thermostat to maintain a constant temperature simulation.
  c.Dynamics.thermostat = 'None'

  # Temperature of the heat bath, used either by a stochastic integrator or the
  # Andersen thermostat to maintain a constant temperature ensemble.
  # c.Dynamics.temp = 300*kelvin

  # OpenMM offers a choice of several different integration methods. Refer to the
  # user guide for details.
  c.Dynamics.integrator = 'VariableVerlet'

  # Pressure target, used by a barostat.
  # c.Dynamics.pressure = 1*atmosphere

  # The frequency (in time steps) at which Monte Carlo pressure changes should be
  # attempted. This option is only invoked when barostat == MonteCarlo.
  # c.Dynamics.barostat_interval = 25

  # Timestep for fixed-timestep integrators.
  # c.Dynamics.dt = 2*femtosecond

  # Tolerance for variable timestep integrators ('VariableLangevin',
  # 'VariableVerlet'). Smaller values will produce a smaller average step size.
  c.Dynamics.tolerance = 0.0001

  #------------------------------------------------------------------------------
  # Simulation configuration
  #------------------------------------------------------------------------------

  # Parameters for the simulation object, including reporters, number of steps,
  # etc

  # First perform local energy minimization, to find a local potential energy
  # minimum near the starting structure.
  c.Simulation.minimize = True

  # Number of steps of simulation to run.
  c.Simulation.n_steps = 1000

  # Frequency, in steps, to save the state to disk in the DCD format.
  c.Simulation.traj_freq = 1000

  # Frequency, in steps, to print summary statistics on the state of the
  # simulation.
  c.Simulation.statedata_freq = 1000

  # Filename to save the resulting trajectory to, in DCD format.
  c.Simulation.traj_file = 'output.dcd'
  ```