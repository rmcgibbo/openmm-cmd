#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import pickle
import os

# openmm
from simtk.unit import nanometer, picosecond, femtosecond, dalton, mole, kilojoule

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class RestartReporter(object):
    def __init__(self, reportInterval, restart_filename, integrator_name, timestep):
        self._reportInterval = reportInterval
        self._restart_filename = restart_filename
        self._integrator_name = integrator_name
        self._timestep = timestep

    def describeNextReport(self, simulation):
        steps = self._reportInterval - simulation.currentStep%self._reportInterval
        return (steps, True, True, True, True)

    def report(self, simulation, state):
        Xfin = state.getPositions() / nanometer
        Vfin = state.getVelocities() / nanometer * picosecond
        if self._integrator_name != "VelocityVerlet":
            # We will attempt to get the velocities at the current time.  First obtain initial velocities.
            v0 = Vfin * nanometer / picosecond
            frc = state.getForces()
            # Obtain masses.
            mass = []
            for i in range(simulation.context.getSystem().getNumParticles()):
                mass.append(simulation.context.getSystem().getParticleMass(i)/dalton)
            mass *= dalton
            # Get accelerations.
            accel = []
            for i in range(simulation.context.getSystem().getNumParticles()):
                accel.append(frc[i] / mass[i] / (kilojoule/(nanometer*mole*dalton)))# / (kilojoule/(nanometer*mole*dalton)))
            accel *= kilojoule/(nanometer*mole*dalton)
            # Propagate velocities backward by half a time step.
            dv = accel
            dv *= (+0.5 * self._timestep)
            vmdt2 = []
            for i in range(simulation.context.getSystem().getNumParticles()):
                vmdt2.append((v0[i]/(nanometer/picosecond)) + (dv[i]/(nanometer/picosecond)))
            # These are the velocities that we store (make sure it is unitless).
            Vfin = vmdt2
        Bfin = state.getPeriodicBoxVectors() / nanometer
        with open(os.path.join(self._restart_filename),'w') as f: pickle.dump((Xfin, Vfin, Bfin),f)

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def read_restart_info(simulation, restart_filename, integrator_name, timestep):
    # Load information from the restart file.
    r_positions, r_velocities, r_boxes = pickle.load(open(restart_filename))
    simulation.context.setPositions(r_positions * nanometer)
    if simulation.topology.getUnitCellDimensions() != None:
        simulation.context.setPeriodicBoxVectors(r_boxes[0] * nanometer,r_boxes[1] * nanometer, r_boxes[2] * nanometer)
    if integrator_name != "VelocityVerlet":
        # We will attempt to reconstruct the leapfrog velocities.  First obtain initial velocities.
        v0 = r_velocities * nanometer / picosecond
        frc = simulation.context.getState(getForces=True).getForces()
        # Obtain masses.
        mass = []
        for i in range(simulation.context.getSystem().getNumParticles()):
            mass.append(simulation.context.getSystem().getParticleMass(i)/dalton)
        mass *= dalton
        # Get accelerations.
        accel = []
        for i in range(simulation.context.getSystem().getNumParticles()):
            accel.append(frc[i] / mass[i] / (kilojoule/(nanometer*mole*dalton)))# / (kilojoule/(nanometer*mole*dalton)))
        accel *= kilojoule/(nanometer*mole*dalton)
        # Propagate velocities backward by half a time step.
        dv = accel
        dv *= (-0.5 * timestep)
        vmdt2 = []
        for i in range(simulation.context.getSystem().getNumParticles()):
            vmdt2.append((v0[i]/(nanometer/picosecond)) + (dv[i]/(nanometer/picosecond)))
        vmdt2 *= nanometer/picosecond
        # Assign velocities.
        simulation.context.setVelocities(vmdt2)
        simulation.context.applyVelocityConstraints(1e-4)
    else:
        simulation.context.setVelocities(r_velocities * nanometer / picosecond)
