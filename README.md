OpenMM on the Command Line
==========================

OpenMM command line app config file framework / parser based on IPython traitlets
system. Every configurable option can be specified in an input config file or
directly on the command line. Command line options override config file
supplied options.

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
  a runnable output config file. The config file always contains the help
  text for every option, so you shouldn't have to consult the documentation
  to figure out what a given flag is (i.e. no 'ntx=7' sander options)
  
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
  
5. Lots of help.
  ```
  $ openmm -h
  
  OpenMM: GPU Accelerated Molecular Dynamics
  ==========================================

  Run a molecular simulaton using the OpenMM toolkit.

  Options
  -------

  --config=<Bytes> (OpenMM.config_file_path)
      Default: 'config.in.py'
      Path to a configuration file to load from. The configuration files contains
      settings for all of the MD options. Every option can be either set in the
      config file and/or the command line. (see `--help-all`).
  --log_level=<Enum> (OpenMM.log_level)
      Default: 'INFO'
      Choices: [0, 10, 20, 30, 40, 50, 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL']
      Set the log level by value or name.
  --out=<Bytes> (OpenMM.config_file_out)
      Default: 'config.out.py'
      Write a config file containing all of the active options used by this
      simulation.

  To see all available configurables, use `--help-all`
  ```

  ```
  $ openmm --help-all
  
  [OpenMM] WARNING | No config file was found.

  OpenMM: GPU Accelerated Molecular Dynamics
  ==========================================

  Run a molecular simulaton using the OpenMM toolkit.

  Options
  -------

  --config=<Bytes> (OpenMM.config_file_path)
      Default: 'config.in.py'
      Path to a configuration file to load from. The configuration files contains
      settings for all of the MD options. Every option can be either set in the
      config file and/or the command line. (see `--help-all`).
  --log_level=<Enum> (OpenMM.log_level)
      Default: 'INFO'
      Choices: [0, 10, 20, 30, 40, 50, 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL']
      Set the log level by value or name.
  --out=<Bytes> (OpenMM.config_file_out)
      Default: 'config.out.py'
      Write a config file containing all of the active options used by this
      simulation.

  General options
  ---------------
  --coords=<Bytes>
      Default: ''
      OpenMM can take a pdb...
  --forcefield=<CaselessStrEnum>
      Default: 'amber99sb-ildn'
      Choices: ['amber96', 'amber99sb', 'amber99sb-ildn', 'amber99sb-nmr', 'amber03', 'amber10']
      Forcefield to use for the protein atoms. For details, consult the
      literature.
  --platform=<CaselessStrEnum>
      Default: None
      Choices: ['Reference', 'OpenCL', 'CUDA']
      OpenMM runs simulations on three platforms: Reference, CUDA, and OpenCL. If
      not specified, the fastest available platform will be selected
      automatically.
  --precision=<CaselessStrEnum>
      Default: None
      Choices: ['Single', 'Mixed', 'Double']
      Level of numeric precision to use for calculations.
  --water=<CaselessStrEnum>
      Default: 'TIP3P'
      Choices: ['SPC/E', 'TIP3P', 'TIP4-Ew', 'TIP5P', 'Implict']
      Forcefield to use for water in the simulation.

  System options
  --------------
  --constraints=<CaselessStrEnum>
      Default: 'HBonds'
      Choices: ['None', 'HBonds', 'AllBonds', 'HAngles']
      Applying constraints to some of the atoms can enable you to take longer
      timesteps.
  --cutoff=<Quantity>
      Default: 1.0*nanometer
      Cutoff for long-range non-bonded interactions. This option is usef for all
      non-bonded methods except for "NoCutoff".
  --ewald_tol=<Float>
      Default: 0.0005
      The error tolerance is roughly equal to the fractional error in the forces
      due to truncating the Ewald summation.
  --gen_temp=<Quantity>
      Default: 300*kelvin
      Temperature used for generating initial velocities. This option is only used
      if rand_vels == True.
  --nb_method=<CaselessStrEnum>
      Default: 'PME'
      Choices: ['NoCutoff', 'CutoffNonPeriodic', 'CutoffPeriodic', 'Ewald', 'PME']
      Method for calculating long range non-bondend interactions. Refer to the
      user guide for a detailed discussion.
  --rand_vels=<Bool>
      Default: True
      Initialize the system with random initial velocities, drawn from the Maxwell
      Boltzmann distribution.
  --rigid_water=<Bool>
      Default: True
      Keep water rigid. Be aware that flexible water may require you to further
      reduce the integration step size, typically to about 0.5 fs.

  Dynamics options
  ----------------
  --barostat=<CaselessStrEnum>
      Default: 'None'
      Choices: ['MonteCarlo', 'None']
      Activate a barostat for pressure coupling. The MC barostat requires
      temperature control (stochastic integrator or Andersen thermostat) to be in
      effect as well.
  --barostat_interval=<Int>
      Default: 25
      The frequency (in time steps) at which Monte Carlo pressure changes should
      be attempted. This option is only invoked when barostat == MonteCarlo.
  --collision_rate=<Quantity>
      Default: 1.0/picosecond
      Friction coefficient, for use with stochastic integrators or the Anderson
      thermostat.
  --dt=<Quantity>
      Default: 2*femtosecond
      Timestep for fixed-timestep integrators.
  --integrator=<CaselessStrEnum>
      Default: 'Langevin'
      Choices: ['Langevin', 'Verlet', 'Brownian', 'VariableLangevin', 'VariableVerlet']
      OpenMM offers a choice of several different integration methods. Refer to
      the user guide for details.
  --pressure=<Quantity>
      Default: 1*atmosphere
      Pressure target, used by a barostat.
  --temp=<Quantity>
      Default: 300*kelvin
      Temperature of the heat bath, used either by a stochastic integrator or the
      Andersen thermostat to maintain a constant temperature ensemble.
  --thermostat=<CaselessStrEnum>
      Default: None
      Choices: ['Andersen', 'None']
      Activate a thermostat to maintain a constant temperature simulation.
  --tolerance=<Float>
      Default: 0.0001
      Tolerance for variable timestep integrators ('VariableLangevin',
      'VariableVerlet'). Smaller values will produce a smaller average step size.

  Simulation options
  ------------------
  --minimize=<Bool>
      Default: True
      First perform local energy minimization, to find a local potential energy
      minimum near the starting structure.
  --n_steps=<Int>
      Default: 1000
      Number of steps of simulation to run.
  --statedata_freq=<Int>
      Default: 1000
      Frequency, in steps, to print summary statistics on the state of the
      simulation.
  --traj_file=<Bytes>
      Default: 'output.dcd'
      Filename to save the resulting trajectory to, in DCD format.
  --traj_freq=<Int>
      Default: 1000
      Frequency, in steps, to save the state to disk in the DCD format.
  ```