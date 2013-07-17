OpenMM on the Command Line
==========================

OpenMM command line app config file framework / parser based on IPython traitlets
system. Every configurable option can be specified in an input config file or
directly on the command line. Command line options override config file
supplied options.

Features
--------

1. Parsing units on the command line.
  ```
  $ openmm --dt 1
  [OpenMM] WARNING | No config file was found.
  [OpenMM] ERROR | The 'dt' trait of the dynamics section must have units of
  femtosecond, but a value without units, 1, was specified. To specify units,
  use a syntax like --dt=2*femtosecond on the command line, or dt = 2*femtosecond
  in the config file.
  ```
  
  Yes, the full power of `simtk.unit` is available. There's also some error
  checking for commonly incorrect parameters.
  
  ```
  $ openmm --dt 1*years
  [OpenMM] WARNING | No config file was found.
  [OpenMM] ERROR | You are likely using too large a timestep. With the
  Langevin or Verlet integrators and bond constraints, a timestep over 2
  femtoseconds is not recommended.

  $ openmm --dt 0.002*angstroms
  [OpenMM] WARNING | No config file was found.
  [OpenMM] ERROR | The 'dt' trait of the dynamics section must have units 
  of femtosecond, but a value in units of angstrom was specified.
  ```

2. A lot of mistakes are typos. We can help.
  ```
  $ openmm --collision_ratee 1/picoseconds
  [OpenMM] WARNING | No config file was found.
  [OpenMM] ERROR | Unrecognized option: 'collision_ratee'. Did you mean
  '--collision_rate'?
  ```

3. Some options have complex dependencies. If a user supplies an option, they
   probably want it to be in effect.
   
  ```
  $ openmm --coords protein.pdb --temp 300*kelvin --integrator Verlet --thermostat None
  [OpenMM] WARNING | No config file was found.
  [OpenMM] ERROR | The temperature target option, 'temp', is only appropriate when
  using a thermostat or stochastic integrator.

  $ openmm --barostat None --pressure 1*atmosphere
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
  # Configuration file for openmm
  # Generated on vspm9, 2013-07-16 20:05:42.082430
  # OpenMM version 5.1
  # Invokation command line: /home/rmcgibbo/envs/latest/bin/openmm --coords /home/rmcgibbo/local/openmm_tests/input.pdb --protein amber99sb-ildn --water=tip3p --dt=1*fs --minimize False --read_restart True --write_restart=True

  #------------------------------------------------------------------------------
  [General]
  #------------------------------------------------------------------------------
  # General options, including the force field, platform, and coordinates.
  #------------------------------------------------------------------------------

  # Supply one or more custom forcefield files, in the OpenMM XML format. This can
  # be used to specify a forcefield for ligands, nonstandard amino acids, etc.
  ffxml = 

  # Level of numeric precision to use for calculations.
  # Choices: [Single, Mixed, Double]
  precision = Mixed

  # Forcefield to use for water in the simulation.
  # Choices: [SPC/E, TIP3P, TIP4-Ew, TIP5P, Implicit, None]
  water = TIP3P

  # OpenMM runs simulations on three platforms: Reference, CUDA, and OpenCL. If
  # not specified, the fastest available platform will be selected automatically.
  # Choices: [Reference, OpenCL, CUDA, NotSpecified]
  platform = NotSpecified

  # OpenMM can take a pdb...
  coords = /home/rmcgibbo/local/openmm_tests/input.pdb

  # Forcefield to use for the protein atoms. For details, consult the literature.
  # Choices: [amber96, amber99sb, amber99sb-ildn, amber99sb-nmr, amber03, amber10,
  # None]
  protein = amber99sb-ildn

  #------------------------------------------------------------------------------
  [System]
  #------------------------------------------------------------------------------
  # Parameters for the system, including the method for calculating nonbonded
  # forces, constraints, and initialization of velocities.
  #------------------------------------------------------------------------------

  # Cutoff for long-range non-bonded interactions. This option is used for all
  # non-bonded methods except for "NoCutoff".
  cutoff = 1.0*nanometer

  # Initialize the system with random initial velocities, drawn from the Maxwell
  # Boltzmann distribution.
  rand_vels = True

  # The error tolerance is roughly equal to the fractional error in the forces due
  # to truncating the Ewald summation.
  ewald_tol = 0.0005

  # Keep water rigid. Be aware that flexible water may require you to further
  # reduce the integration step size, typically to about 0.5 fs.
  rigid_water = True

  # Temperature used for generating initial velocities. This option is only used
  # if rand_vels == True.
  gen_temp = 300*kelvin

  # Method for calculating long range non-bondend interactions. Refer to the user
  # guide for a detailed discussion.
  # Choices: [NoCutoff, CutoffNonPeriodic, CutoffPeriodic, Ewald, PME]
  nb_method = PME

  # Applying constraints to some of the atoms can enable you to take longer
  # timesteps.
  # Choices: [None, HBonds, AllBonds, HAngles]
  constraints = HBonds

  #------------------------------------------------------------------------------
  [Dynamics]
  #------------------------------------------------------------------------------
  # Parameters for the integrator, thermostats and barostats.
  #------------------------------------------------------------------------------

  # Friction coefficient, for use with stochastic integrators or the Anderson
  # thermostat.
  collision_rate = 1.0/picosecond

  # Activate a barostat for pressure coupling. The MC barostat requires
  # temperature control (stochastic integrator or Andersen thermostat) to be in
  # effect as well.
  # Choices: [MonteCarlo, MonteCarloAnisotropic, None]
  barostat = None

  # Activate a thermostat to maintain a constant temperature simulation.
  # Choices: [Andersen, None]
  thermostat = None

  # Temperature of the heat bath, used either by a stochastic integrator or the
  # Andersen thermostat to maintain a constant temperature ensemble.
  temp = 300*kelvin

  # Pressure target, used by a barostat.
  # pressure = 1*atmosphere

  # OpenMM offers a choice of several different integration methods. Refer to the
  # user guide for details.
  # Choices: [Langevin, Verlet, Brownian, VariableLangevin, VariableVerlet,
  # VelocityVerlet]
  integrator = Langevin

  # Switch for scaling the x-axis,  used by the Monte Carlo anisotropic barostat.
  # scalex = True

  # Switch for scaling the y-axis,  used by the Monte Carlo anisotropic barostat.
  # scaley = True

  # Switch for scaling the z-axis,  used by the Monte Carlo anisotropic barostat.
  # scalez = True

  # Pressure target, used by the Monte Carlo anisotropic barostat.
  # pressure3 = [1, 1, 1]

  # The frequency (in time steps) at which Monte Carlo pressure changes should be
  # attempted. This option is only invoked when barostat in [MonteCarlo,
  # MonteCarloAnisotropic].
  # barostat_interval = 25

  # Timestep for fixed-timestep integrators.
  dt = 1*femtosecond

  # Tolerance for variable timestep integrators ('VariableLangevin',
  # 'VariableVerlet'). Smaller values will produce a smaller average step size.
  # tolerance = 0.0001

  #------------------------------------------------------------------------------
  [Simulation]
  #------------------------------------------------------------------------------
  # Parameters for the simulation, including the mode and frequency with which
  # files are saved to disk, the number of steps, etc.
  #------------------------------------------------------------------------------

  # Filename for  reading/writing the restart file, in Python pickle format.
  restart_file = restart.p

  # First perform local energy minimization, to find a local potential energy
  # minimum near the starting structure.
  minimize = False

  # Frequency, in steps, to save the restart file in Python pickle format.
  restart_freq = 5000

  # Filename to save the resulting trajectory to, in DCD format.
  traj_file = output.dcd

  # Switch for whether to read restart information from file.
  read_restart = True

  # Frequency, in steps, to print summary statistics on the state of the
  # simulation.
  statedata_freq = 1000

  # Number of steps of simulation to run.
  n_steps = 10000

  # Switch for whether to write restart information to file.
  write_restart = True

  # Frequency, in steps, to save the state to disk in the DCD format.
  traj_freq = 1000


  ```
