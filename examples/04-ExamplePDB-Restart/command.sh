openmm --coords input.pdb --protein amber99sb --water tip3p | tee openmm.out
openmm --coords input.pdb --protein amber99sb --water tip3p --read_restart True | tee openmm1.out
