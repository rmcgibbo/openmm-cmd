#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import time

# openmm
from simtk import unit
from simtk.openmm.app import StateDataReporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ProgressReporter(StateDataReporter):
    def __init__(self, file, reportInterval, totalSteps):
        super(ProgressReporter, self).__init__(file, reportInterval, step=False, time=True,
            potentialEnergy=True, kineticEnergy=True, totalEnergy=True,
            temperature=True)

        self._totalSteps = totalSteps

    def _initializeConstants(self, simulation, state):
        if simulation.topology.getUnitCellDimensions() is not None:
            self._volume = True
            self._density = True
        
        # this needs to come after _density and _volume are set so
        # that the mass gets computed, if needed.
        super(ProgressReporter, self)._initializeConstants(simulation)

        # initialize these as late as possible, so that as little initialization
        # code gets counted in the elapsed walltime. When that happens, it
        # makes it look like the simulation is getting faster and faster,
        # since that time is being amoritized out.
        self._initialWallTime = time.time()
        self._initialStep = simulation.currentStep
        self._initialSimTime = state.getTime()

    def _constructReportValues(self, simulation, state):
        progressPercent = 100 * float(simulation.currentStep - self._initialStep) / self._totalSteps
        if progressPercent > 0:
            timeLeft = (time.time() - self._initialWallTime) * (100.0 - progressPercent) / progressPercent
            
            elapsedSim = (state.getTime() - self._initialSimTime).value_in_unit(unit.nanoseconds)
            walltime = ((time.time() - self._initialWallTime)*unit.seconds).value_in_unit(unit.days)
            rate = elapsedSim / walltime                   
        else:
            timeLeft = '??'
            rate = 0
        
        values = [progressPercent, timeLeft, rate] + super(ProgressReporter, self)._constructReportValues(simulation, state)
        return values
        
    def _constructHeaders(self):
        headers = [('Progress', '(%)'),
                   ('E.T.A', '(s)'),
                   ('Speed', '(ns/day)'),
                   ('Time',  '(ps)'),
                   ('P.E.', '(kJ/mol)'),
                   ('K.E.', '(kJ/mol)'),
                   ('Total E.', '(kJ/mol)'),
                   ('Temp', '(K)'),
                  ]
        
        widths =  [8,          13,      8,        13,       15, 
                   13,         13,      13,       8]
        formats = ['%7.3f%%', '%13.5s', '%8.2f', '%13.5f', '%15.5f',
                   '%13.5f', '%13.5f', '%13.5f', '%8.2f']

        if self._volume:
            headers.append(('Vol', '(nm^3)'))
            formats.append('%8.2f')
            widths.append(8)
        if self._density:
            headers.append(('Rho', '(g/mL)'))
            formats.append('%8.2f')
            widths.append(8)
            
        self._formats = formats
        
        row1, row2 = zip(*headers)
        headerwidths = ['%{w}s'.format(w=w) for w in widths]
        print >>self._out, ' '.join(f % e for f, e in zip(headerwidths, row1))
        print >>self._out, ' '.join(f % e for f, e in zip(headerwidths, row2))

    
    def report(self, simulation, state):
        if not self._hasInitialized:
            self._initializeConstants(simulation, state)
            self._constructHeaders()
            self._hasInitialized = True
        
        # Check for errors.
        self._checkForErrors(simulation, state)

        # Query for the values
        values = self._constructReportValues(simulation, state)

        print >>self._out, ' '.join(f % v for f, v in zip(self._formats, values))
