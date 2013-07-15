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
openmm: error: The 'dt' trait of the dynamics section must have units of
femtosecond, but a value without units, 1, was specified. To specify units,
use a syntax like --dt=2*femtosecond on the command line, or c.Dynamics.dt =
2*femtosecond in the config file.
```

2. Did you mean?

```
$ openmm --collision_ratee=1/picoseconds
[OpenMM] WARNING | No config file was found.
openmm: error: Unrecognized option: 'collision_ratee'. Did you mean
'collision_rate'?
```

3. Ensuring that supplied configuration options actually make sense

```
$ openmm --temp=300*kelvin --integrator=Verlet
[OpenMM] WARNING | No config file was found.
openmm: error: The temperature target option, 'temp', is only appropriate when
using a thermostat or stochastic integrator.

$ openmm --barostat=None  --pressure=1*atmosphere
[OpenMM] WARNING | No config file was found.
openmm: error: The pressure target option, 'pressure', is only appropriate
when using the Monte Carlo barostat.
```