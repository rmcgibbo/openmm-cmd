#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import os
import shutil
import json
import xdrlib

import simtk.openmm as mm

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class CheckpointReporter(object):
    """Reporter to save checkpoint files. Checkpoint files are hardware and
    platform specific -- they can only be reinstantiated on the same hardware
    they were produced on. Because of that specificity, they are able to save
    almost all of the data structures used, including things like the state
    of the internal random number generators.
    """
    def __init__(self, path, reportInterval, backupPath=None):
        self._report_interval = reportInterval
        self._open = True
        self._initialized = False
        
        self._path = path
        if backupPath is None:
            self._backup_path = '%s.bak' % path
        else:
            self._backup_path = backupPath
        self._static_data_length = None

    def _initialize(self, simulation):
        """Delayed initalization -- done only once we have a handle to the
        simulation"""
        
        platform = simulation.context.getPlatform()
        # Get all of the platform properties. We are going to make sure these
        # match when we instantiate the checkpoint file back up.
        properties = {'OpenMMVersion': platform.getOpenMMVersion(),
                      'PlatformName': platform.getName()}
        for key in platform.getPropertyNames():
            properties[key] = platform.getPropertyValue(simulation.context, key)

        self._write_static_data(properties, simulation.context.getIntegrator(),
                                simulation.context.getSystem())

    def _write_static_data(self, platformProperties, integrator, system):
        packer = xdrlib.Packer()
        packer.pack_string(json.dumps(platformProperties))
        packer.pack_string(mm.XmlSerializer.serialize(integrator))
        packer.pack_string(mm.XmlSerializer.serialize(system))
        
        buf = packer.get_buffer()
        with open(self._path, 'wb') as f:
            f.write(buf)
            self._static_data_length = f.tell()

    def _create_checkpoint(self, context):
         packer = xdrlib.Packer()
         packer.pack_string(context.createCheckpoint())
         return packer.get_buffer()

    def describeNextReport(self, simulation):
        """Get information about the next report this object will generate.

        Parameters:
         - simulation (Simulation) The Simulation to generate a report for
        Returns: A five element tuple.  The first element is the number of steps until the
        next report.  The remaining elements specify whether that report will require
        positions, velocities, forces, and energies respectively.
        """
        steps = self._report_interval - simulation.currentStep % self._report_interval
        return (steps, False, False, False, False)

    def report(self, simulation, state=None):
        """Generate a report.

        Parameters:
         - simulation (Simulation) The Simulation to generate a report for
         - state (State) The current state of the simulation
        """
        if not self._initialized:
            self._initialize(simulation)
            self._initialized = True

        check = self._create_checkpoint(simulation.context)
        # copy the current checkpoint to the backup before writing
        # the new backup
        shutil.copy2(self._path, self._backup_path)

        with open(self._path, 'r+b') as f:
            f.seek(self._static_data_length)
            f.write(check)


    def __del__(self):
        os.unlink(self._backup_path)
